FROM alpine:3.20
CMD ["nc", "-lkv", "-s", "0.0.0.0", "-p", "8080", "-e", "/bin/cat"]
