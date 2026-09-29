#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static void touch_page(unsigned char *region, long page_size, int page_index) {
    region[(size_t)page_index * (size_t)page_size] =
        (unsigned char)((page_index + 1) & 0xff);
}

static int migrate_to(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0)
        return -1;
    for (int i = 0; i < 100000; ++i) {
        if (sched_getcpu() == cpu)
            return cpu;
    }
    return -1;
}

int main(int argc, char **argv) {
    const char *control_path = NULL, *status_path = NULL;
    int max_pages = 16;
    for (int i=1;i<argc;++i) {
        if (!strcmp(argv[i],"--control") && i+1<argc) control_path=argv[++i];
        else if (!strcmp(argv[i],"--status") && i+1<argc) status_path=argv[++i];
        else if (!strcmp(argv[i],"--max-pages") && i+1<argc) max_pages=atoi(argv[++i]);
        else return 2;
    }
    if (!control_path || !status_path || max_pages < 2) return 2;

    long page_size=sysconf(_SC_PAGESIZE);
    if (page_size<=0) return 2;
    size_t region_size=(size_t)max_pages*(size_t)page_size;
    unsigned char *region=mmap(NULL,region_size,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (region==MAP_FAILED) return 2;

    FILE *status=fopen(status_path,"a");
    if (!status) return 2;
    setvbuf(status,NULL,_IOLBF,0);

    int touched=0;
    fprintf(status,"READY cpu=%d page_size=%ld touched=0\n",
        sched_getcpu(),page_size);

    int fd=open(control_path,O_RDWR|O_CLOEXEC);
    if (fd<0) return 2;
    FILE *control=fdopen(fd,"r");
    if (!control) return 2;

    char line[128];
    while (fgets(line,sizeof(line),control)) {
        if (!strncmp(line,"MIGRATE_TOUCH ",14)) {
            int cpu=atoi(line+14);
            int seen=migrate_to(cpu);
            if (seen != cpu) {
                fprintf(status,"ERROR migrate_touch cpu=%d seen=%d\n",cpu,seen);
                continue;
            }
            /* Critical invariant: no status I/O between arrival on S and touch. */
            touch_page(region,page_size,touched++);
            fprintf(status,"MIGRATE_TOUCH cpu=%d count=%d\n",seen,touched);
        } else if (!strncmp(line,"MIGRATE ",8)) {
            int cpu=atoi(line+8);
            int seen=migrate_to(cpu);
            if (seen != cpu) {
                fprintf(status,"ERROR migrate cpu=%d seen=%d\n",cpu,seen);
                continue;
            }
            /* Deliberately reproduces the old post-migration receipt path. */
            fprintf(status,"MIGRATE cpu=%d touched=%d\n",seen,touched);
        } else if (!strncmp(line,"TOUCH_ONE",9)) {
            touch_page(region,page_size,touched++);
            fprintf(status,"TOUCH cpu=%d count=%d\n",sched_getcpu(),touched);
        } else if (!strncmp(line,"STOP",4)) {
            fprintf(status,"STOP cpu=%d touched=%d\n",sched_getcpu(),touched);
            break;
        } else {
            fprintf(status,"ERROR command\n");
        }
    }
    fclose(control);
    fclose(status);
    munmap(region,region_size);
    return 0;
}
