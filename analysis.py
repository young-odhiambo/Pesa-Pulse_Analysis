import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests

API_URL = "https://jsonplaceholder.typicode.com/users"
OUTPUT_DIR = Path("output")


def get_customers(url: str = API_URL) -> list[dict]:
    """Fetch the customer list. Report failures clearly instead of crashing."""
    try:
        response = requests.get(url,timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.request.exceptions.RequestException as error:
        print(f"Error fetching customers: {error}")
        return []

customers = get_customers()
print(customers)


def explore(record: dict, indent: int = 0) -> None:
    """Print every key in a (possibly nested) record with its type, indented by depth."""
    
    pad = "     " * indent
    if isinstance(record, dict):
        for key, value in record.items():
            print(f"{pad}{key}:{type(value).__name__}") #class <str>
            explore(value, indent + 1)
    elif isinstance(record, list):
        for i, item in enumerate(record):
            if isinstance(item, (dict, list)):
                print(f"{pad}{i}:{type(item).__name__}")
                explore(item, indent + 1)

results = explore(customers)
print(results)


def extract_attributes(customers: list[dict]) -> list[dict]:
    """Return one flat dict per customer with the attributes listed in the task."""
    rows = [
        # creating an empty list , inisde it will have many dictionaries, each dictinary has individual attributes from the jason file(a nested dictinary)
    ]
    # customers is the whole jason file with (eg 500 customers), c stands for one out of the 500 customers.
    for c in customers:
        rows.append({
            'id': c['id'],
            'name': c['name'],
            "username": c["username"],
            "email": c["email"],
            "email_domain": c["email"].split("@")[-1].lower(),
            "phone": c["phone"],
            "city": c["address"]["city"],
            "zipcode": c["address"]["zipcode"],
            "latitude": float(c["address"]["geo"]["lat"]),
            "longitude": float(c["address"]["geo"]["lng"]),
            "company": c["company"]["name"],
            "website": c["website"],
        })
    return rows

result_x = extract_attributes(customers)
print(result_x)

def unique_cities(customers: list[dict]) -> set[str]:
    """Return the set of distinct cities."""
    return {c['address']['city'] for c in customers}

cities = unique_cities(customers)
print(cities)


def city_counts(customers: list[dict]) -> dict[str, int]:
    """Count customers per city using a loop and/or a dict comprehension (no Counter, no pandas)."""
    counts = {}
    for c in customers:
        city = c['address']['city']
        counts[city] = counts.get(city, 0) + 1
    return counts


def email_domain_counts(rows: list[dict]) -> dict[str, int]:
    """Count customers per email top-level domain (e.g. 'biz', 'tv')."""
    domains = [row["email_domain"] for row in rows] 
    
    return {
            domain: domains.count(domain)
            for domain in sorted(set(domains))
        }
def tld_counts(rows: list[dict]) -> dict[str, int]:
    """Count customers per top-level domain (biz, org, ...)."""
    tlds = [row["email_domain"].rsplit(".", 1)[-1] for row in rows]
    return {tld: tlds.count(tld) for tld in set(tlds)}

def sort_counts(counts):
    """Most to least common; ties broken alphabetically so output is stable."""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))

def print_counts(title, counts):
    print(f'\n{title}')
    for label, number in sort_counts(counts):
        print(f'    {label:<20} {number}')


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def plot_distribution(counts: dict[str, int], path: Path,
                      title: str = "Customers by city",
                      xlabel: str = "Customers") -> None:
    """Save a labelled chart of the distribution to path."""
    ordered = sort_counts(counts)
    labels = [label for label, _ in ordered][::-1]   # reversed: barh draws bottom-up
    values = [number for _, number in ordered][::-1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(labels, values)
    ax.set_title(title, fontsize=14, weight="bold")
    ax.set_xlabel(xlabel)
    ax.xaxis.get_major_locator().set_params(integer=True)  # no "0.5 customers"
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main(customers=None):
    customers = customers if customers is not None else get_customers(API_URL)
    if not customers:
        print("No data to analyse. Stopping.")
        return

    print(f"Fetched {len(customers)} customer records.\n")
    print("Structure of one record:")
    explore(customers[0])

    rows = extract_attributes(customers)

    cities = unique_cities(customers)
    print(f"\n{len(cities)} unique cities across {len(rows)} customers.")
    if len(cities) == len(rows):
        print("Every customer is in a different city, so city can't group anyone.")

    by_city = city_counts(customers)
    by_domain = email_domain_counts(rows)
    by_tld = tld_counts(rows)
    print_counts("Customers by city:", by_city)
    print_counts("Customers by email domain:", by_domain)
    print_counts("Customers by email TLD:", by_tld)

    df = to_dataframe(rows)
    print(f"\nDataFrame shape: {df.shape}")
    print(df.dtypes)
    assert df["city"].value_counts().to_dict() == by_city, "pandas disagrees on cities"
    assert df["email_domain"].value_counts().to_dict() == by_domain, "pandas disagrees on domains"
    print("\npandas value_counts() matches the hand-written counts.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_DIR / "customers.csv", index=False)
    city_df = pd.DataFrame(sort_counts(by_city), columns=["city", "customers"])
    city_df.to_csv(OUTPUT_DIR / "city_counts.csv", index=False)

    plot_distribution(by_city, OUTPUT_DIR / "customer_distribution.png")
    plot_distribution(by_tld, OUTPUT_DIR / "customer_distribution_tld.png",
                      title="Customers by email domain type (TLD)")
    print("Saved CSVs and charts to output/")


if __name__ == "__main__":
    main()