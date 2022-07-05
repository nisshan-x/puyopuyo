from puyo import Puyo


def main():

    while True:
        puyo = Puyo()

        while True:
            game_restart = puyo.loop()
            if game_restart:
                break

        del puyo


if __name__ == "__main__":
    main()
