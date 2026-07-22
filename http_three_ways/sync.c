#include "common.h"
#include <pthread.h>
#include <signal.h>

static int write_all(int fd, const void *buf, size_t towrite){
    const char *p = buf;
    while(towrite){
        ssize_t w = write(fd, p, towrite);
        if(w < 0){
            if(errno == EINTR) continue;
            return -1;
        }
        p += w;
        towrite -= (size_t)w;
    }
    return 0;
}

static void send_response(int conn, const char *path){
    char headers[512];
    int file_fd = -1;
    if(path != NULL){
        char full[204];
        snprintf(full, sizeof(full), "%s%s", DOCROOT, path);
        file_fd = open(full, O_RDONLY);
    }

    if(file_fd < 0){
        int header_length = build_404(headers, sizeof(headers));
        write_all(conn, headers, header_length);
        return;
    }

    int header_length = build_ok_headers(headers, sizeof(headers), mime_for(path));
    if(write_all(conn, headers, header_length) < 0){
        close(file_fd);
        return;
    }

    char body_buf[IO_BUF];
    for(;;){
        ssize_t r = read(file_fd, body_buf, sizeof(body_buf));
        if(r < 0){
            if(errno == EINTR) continue;

            break;
        }
        if(r == 0) break;
        if(write_all(conn, body_buf, r) < 0) break;
    }
    close(file_fd);
}

// returns -1 if cxn closes early, -2 if headers cannot be parsed.
static int parse_request(int conn, char *path, size_t path_size){
    char req_buf[MAX_REQ_BUF];
    size_t offset = 0;

    while(offset < sizeof(req_buf)){
        ssize_t r = read(conn, req_buf + offset, sizeof(req_buf) - offset);
        if(r < 0){
            if(errno == EINTR) continue;
            return -1;
        }
        if(r == 0) return -1;
        offset += (size_t)r;
        if(offset >= 4 && memmem(req_buf, offset, "\r\n\r\n", 4)) break;
    }

    if(parse_http_get(req_buf, offset, path, path_size) < 0) return -2;
    return 0;
}

static void *serve(void *arg){
    int conn = (int)(intptr_t)arg;
    char path[1024];
    int rc = parse_request(conn, path, sizeof(path));
    if(rc == 0) send_response(conn, path);
    else if(rc == -1) {}
    else if(rc == -2) send_response(conn, NULL);

    close(conn);
    return NULL;
}

int main(int argc, char**argv){
    signal(SIGPIPE, SIG_IGN);

    uint16_t port = (argc > 1) ? (uint16_t)atoi(argv[1]) : 8080;
    int sfd = listen_socket(port);
    fprintf(stderr, "sync (thread per request) server on :%u\n", port);

    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

    for(;;){
        int conn = accept(sfd, NULL, NULL);
        if (conn < 0){
            if (errno == EINTR) continue;

            perror("accept");
            break;
        }

        pthread_t tid;
        if(pthread_create(&tid, &attr, serve, (void *)(intptr_t)conn) != 0){
            perror("pthread_create");
            close(conn);
        }
    }
    pthread_attr_destroy(&attr);
    return 0;
}
