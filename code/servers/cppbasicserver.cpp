#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <iostream>

void echo_handler(const sockaddr_in& addr, int request) {
  while (true) {
    char buffer[8192] = {0};
    int bytes = -1;
    if ((bytes = read(request, buffer, sizeof(buffer))) < 0) {
      perror("error reading");
      exit(EXIT_FAILURE);
    }
    if (bytes == 0) {
      break;
    }
    if (send(request, buffer, bytes, 0) < 0) {
      perror("error sending");
      exit(EXIT_FAILURE);
    }
  }
  if (close(request) < 0) {
      perror("error closing");
      exit(EXIT_FAILURE);
  }
}


void echo_server(int port, int backlog=5) {
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);
  if (sockfd == 0) {
    perror("socket creation failed");  // use errno for error message
    exit(EXIT_FAILURE);
  }
  int opt = 1;
  if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
    perror("setsock opt failed");
    exit(EXIT_FAILURE);
  }

  sockaddr_in address;
  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons(port);
  if (bind(sockfd, (sockaddr *)&address, sizeof(address)) < 0) {
    perror("bind");
    exit(EXIT_FAILURE);
  }
  if (listen(sockfd, backlog) < 0) {
    perror("bind");
    exit(EXIT_FAILURE);
  }
  while (true) {
    struct sockaddr_in peer;
    socklen_t len = sizeof(peer);
    int request = accept(sockfd, (sockaddr *)&peer, &len);
    if (request < 0) {
      perror("accept");
      exit(EXIT_FAILURE);
    }
    echo_handler(peer, request);  // blocking
  }
}


int main() {
  echo_server(25000);
}
