import argparse
import os


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="hebrewenglish", description="Serve the Davar lexicon page.")
    parser.add_argument("--host", default="0.0.0.0", help="address to listen on (default: %(default)s)")
    parser.add_argument(
        "--port",
        type=int,
        # Container hosts such as Render and Cloud Run say which port to use through PORT
        default=int(os.environ.get("PORT", 8080)),
        help="port to listen on, or the PORT environment variable (default: %(default)s)",
    )
    parser.add_argument(
        "--show",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="open the page in a browser once the server starts (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    # Imported only now, since loading the lexicon takes a while and --help should not wait for it
    from hebrewenglish.frontend.app import App

    app = App()
    app.run(host=args.host, port=args.port, show=args.show)


if __name__ == "__main__":
    main()
