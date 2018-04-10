#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

void echo_handler(const sockaddr_in& addr, int request) {
  while (true) {
    char buffer[8192] = {0};
    int bytes = read(request, buffer, sizeof(buffer));
    if (bytes == 0) {
      break;
    }
    send(request, buffer, bytes, 0);
  }
  close(request);
}


void echo_server(int port, int backlog=5) {
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);
  int opt = 1;
  setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

  sockaddr_in address;
  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons(port);
  bind(sockfd, (sockaddr *)&address, sizeof(address));
  listen(sockfd, backlog);

  while (true) {
    struct sockaddr_in peer;
    socklen_t len = sizeof(peer);
    int request = accept(sockfd, (sockaddr *)&peer, &len);
    echo_handler(peer, request);  // blocking
  }
}


int main() {
  echo_server(25000);
}
