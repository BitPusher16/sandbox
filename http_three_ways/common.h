#pragma once

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define DOCROOT "./"
#define MAX_REQ_BUF 4096
#define IO_BUF 16384

static inline int listen_socket(uint16_t port){
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket");
        exit(1);
    }

    int yes = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);

    if(bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0){
        perror("bind");
        exit(1);
    }

    if(listen(fd, 128) < 0){
        perror("listen");
        exit(1);
    }
    return fd;
}

static inline int parse_http_get(const char *req, size_t len, char *out, size_t n){
    if(len < 5 || strncmp(req, "GET ", 4) != 0) return -1;

    const char *p = req + 4;
    const char *sp = memchr(p, ' ', len - 4);
    if(!sp) return -1;

    size_t plen = (size_t)(sp - p);
    if (plen == 0 || plen >= n) return -1;
    if (p[0] != '/') return -1;

    memcpy(out, p, plen);
    out[plen] = 0;

    if(plen == 1){
        if(n < sizeof("/index.html")) return -1;
        memcpy(out, "/index.html", sizeof("/index.html"));
    }
    return 0;
}

static inline const char *mime_for(const char *path) {
  const char *dot = strrchr(path, '.');
  if (!dot) return "application/octet-stream";
  if (!strncmp(dot, ".html", sizeof(".html"))) return "text/html";
  if (!strncmp(dot, ".css",  sizeof(".css")))  return "text/css";
  if (!strncmp(dot, ".js",   sizeof(".js")))   return "application/javascript";
  if (!strncmp(dot, ".json", sizeof(".json"))) return "application/json";
  if (!strncmp(dot, ".png",  sizeof(".png")))  return "image/png";
  if (!strncmp(dot, ".jpg",  sizeof(".jpg")) ||
      !strncmp(dot, ".jpeg", sizeof(".jpeg"))) return "image/jpeg";
  if (!strncmp(dot, ".txt",  sizeof(".txt")))  return "text/plain";
  return "application/octet-stream";
}

static inline int build_ok_headers(char *buf, size_t n, const char *mime) {
  return snprintf(buf, n,
                  "HTTP/1.1 200 OK\r\n"
                  "Content-Type: %s\r\n"
                  "Connection: close\r\n"
                  "\r\n",
                  mime);
}

static inline int build_404(char *buf, size_t n) {
  return snprintf(buf, n,
                  "HTTP/1.1 404 Not Found\r\n"
                  "Content-Type: text/plain\r\n"
                  "Connection: close\r\n"
                  "\r\n"
                  "404 Not Found\n");
}

















