import os
import requests
import json

class PromoOptionClient:
    """
    A client to interact with the PromoOpción API.
    """
    API_BASE_URL = "https://promocionalesenlinea.net/api"

    def __init__(self, user, password):
        """
        Initializes the client with user credentials.
        """
        if not user or not password:
            raise ValueError("User and password cannot be empty.")
        self.user = user
        self.password = password
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_all_products(self):
        """
        Retrieves the full product catalog.
        This corresponds to the 'API de ficha técnica de Productos (JSON)'.
        """
        endpoint = f"{self.API_BASE_URL}/all-products"
        payload = {
            "user": self.user,
            "password": self.password
        }

        try:
            # Set a long timeout as this request can take a while
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=120)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

            data = response.json()

            if data.get("success") is True:
                return data.get("response", [])
            else:
                error_message = data.get("respusta", "Unknown API error")
                raise Exception(f"API returned an error: {error_message}")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            raise

if __name__ == '__main__':
    """
    This block allows for direct testing of the client.
    It uses credentials passed as environment variables for security.
    """
    print("Testing PromoOptionClient...")

    # In a real environment, these would be set securely.
    # For this test, we'll use the known credentials as a fallback.
    promo_user = os.getenv("PROMO_USER", "MTY4895")
    promo_password = os.getenv("PROMO_PASSWORD", "zzWZqF2ubPKCLSkttula")

    if not promo_user or not promo_password:
        print("Error: PROMO_USER and PROMO_PASSWORD must be available for testing.")
    else:
        try:
            client = PromoOptionClient(user=promo_user, password=promo_password)
            print("Client initialized. Fetching all products...")

            products = client.get_all_products()

            print(f"Successfully fetched {len(products)} products.")
            if products:
                print("\n--- Sample Product (First Product) ---")
                # Using json.dumps for pretty printing
                print(json.dumps(products[0], indent=2, ensure_ascii=False))
                print("--------------------------------------")

            print("\nPromoOptionClient test successful!")

        except Exception as e:
            print(f"An error occurred during client testing: {e}")
