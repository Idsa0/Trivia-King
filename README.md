# Trivia King👑

## Introduction

This project was written by [Idan Saltzman](https://github.com/Idsa0)
and [Omer Ben Hamo](https://github.com/omerbenhamo) for the course _Introduction to Data Communications_.

Trivia King is a client-server application designed to implement a trivia contest. Players receive random true or false
facts and must answer correctly as quickly as possible.

### Features

- **Client-Server Architecture:** Supports multiple players connecting to a single server.
- **True/False Trivia Questions:** Players respond with true or false answers.
- **Multiplayer Support:** Allows for competitive trivia games between multiple players.
- **Network Communication:** Uses UDP for server offers and TCP for game interactions.

## Running Instructions

### Requirements

- **Python 3.x**

### Running the Server

1. Navigate to the root directory of the project.
2. Run the server script using Python:
   ```sh
   ./run_server.bat
   ```

### Running the Client

1. Navigate to the root directory of the project.
2. Run the client script using Python:
   ```sh
   ./run_client.bat
   ```

## Example Run

1. **Server Start:**
    - Team Mystic starts the server.
    - Server prints: `Server started, listening on IP address [Server IP]`.
    - Server sends offer announcements via UDP broadcast every second.

2. **Client Start:**
    - Players Alice, Bob, and Charlie start their clients.
    - Clients print: `Client started, listening for offer requests...`.
    - Clients receive offer and
      print: `Received offer from server “Mystic” at address [Server IP], attempting to connect...`.

3. **Game Connection:**
    - Each client connects to the server over TCP.
    - Clients send player names over TCP.

4. **Game Start:**
    - Server sends a welcome message and a trivia statement.
    - Players respond with true (`Y, T, 1`) or false (`N, F, 0`).

5. **Game Play:**
    - Server and clients print messages as they are sent and received.
    - Correct answers win, incorrect answers disqualify players.

6. **Game End:**
    - Server sends a summary message: `Game over! Congratulations to the winner: [Winner]`.
    - Server and clients return to listening for new game offers.
