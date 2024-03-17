#include <stdio.h>
#include <signal.h>
#include <unistd.h>

int main(void)
{
    if (setuid(0) < 0)
    {
        perror("setuid");
        return 1;
    }

    int ret = kill(-1, SIGKILL);

    if (ret < 0)
    {
        perror("kill");
        return 1;
    }

    return 0;
}