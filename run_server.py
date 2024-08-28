if __name__ == "__main__":
    import sys
    import src.server.trivia_server as s

    if len(sys.argv) > 1:
        server = s.TriviaServer(sys.argv[1])
    else:
        server = s.TriviaServer()

    server.start()
