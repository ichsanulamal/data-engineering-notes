import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import pandas_gbq
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "/home/al/projects/creds/ichsanul-dev-cc6f799c9121.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)


def fetch_data(url):
    """
    Fetches HTML data from a given URL and returns it as a DataFrame.
    """
    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    response = requests.get(url, headers=header)
    response.raise_for_status()  # Raise an exception for HTTP errors
    df = pd.read_html(StringIO(response.text))[0]
    return df


def transform_columns(df):
    """
    Transforms DataFrame with pairs of columns into a DataFrame with two columns: 'name' and 'price'.
    """
    new_df = pd.DataFrame()
    for i in range(0, len(df.columns), 2):
        pair = df.iloc[:, i : i + 2]
        pair.columns = ["name", "price"]
        new_df = pd.concat([new_df, pair], axis=0, ignore_index=True)
    return new_df


def main():
    links = [
        "motherboard.html",
        "proc.html",
        "storage.html",
        "memory.html",
        "lcd.html",
        "casing.html",
        "psu.html",
        "vga.html",
        "mcardflashdisk.html",
        "keymouse.html",
        "audio.html",
        "cooler.html",
        "aksesoris.html",
        "networking.html",
        "printer.html",
        "office.html",
        "tinta.html",
        "software.html",
        "ups-stabilizer.html",
        "notebook.html",
        "partnotebook.html",
        "gadget.html",
        "pcbranded.html",
        "projector.html",
        "server.html",
        "rackserver.html",
    ]

    dataframes = {}
    for link in links:
        category = link.removesuffix(".html")
        url = f"https://viraindo.net/{link}"

        try:
            df = fetch_data(url)
            df = transform_columns(df)
            dataframes[category] = df
            print("Processed", category, df.shape)
        except Exception as e:
            print(f"Error fetching data for {category}: {e}")

    combined_df = pd.concat(
        [df.assign(category=cat) for cat, df in dataframes.items()], ignore_index=True
    )

    combined_df = combined_df[
        (combined_df["price"].notna()) & (combined_df["price"] != "Call")
    ]
    combined_df = combined_df.drop_duplicates(subset=["name"])

    combined_df["inserted_at"] = datetime.now().date()

    combined_df.to_csv("viraindo_raw.csv", index=False)

    table_id = "de_zoomcamp.viraindo_raw"
    pandas_gbq.to_gbq(
        dataframe=combined_df,
        credentials=credentials,
        destination_table=table_id,
        if_exists="append",
    )

    print("Success")


if __name__ == "__main__":
    main()
