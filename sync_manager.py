import os
from promooption_client import PromoOptionClient
from shopify_client import ShopifyClient

class SyncManager:
    """
    Orchestrates the synchronization of products from PromoOpción to Shopify.
    """

    def __init__(self):
        """
        Initializes the clients needed for the synchronization.
        """
        self.promo_user = os.getenv("PROMO_USER", "MTY4895")
        self.promo_password = os.getenv("PROMO_PASSWORD", "zzWZqF2ubPKCLSkttula")
        self.shopify_domain = os.getenv("SHOPIFY_URL", "promotienda-mx.myshopify.com")
        self.shopify_token = os.getenv("SHOPIFY_TOKEN", "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")

        self.promo_client = PromoOptionClient(user=self.promo_user, password=self.promo_password)
        self.shopify_client = ShopifyClient(shop_url=self.shopify_domain, api_token=self.shopify_token)
        print("SyncManager initialized with both clients.")

    def run_full_sync(self, product_limit=None):
        """
        Runs the full synchronization process.
        :param product_limit: An optional integer to limit the number of products processed for testing.
        """
        print("\n--- Starting Full Product Sync ---")

        try:
            # 1. Fetch all products from the supplier
            print("Fetching products from PromoOpción...")
            all_products = self.promo_client.get_all_products()
            print(f"Found {len(all_products)} total products from supplier.")

            if product_limit:
                print(f"Processing a limit of {product_limit} products for this run.")
                products_to_process = all_products[:product_limit]
            else:
                products_to_process = all_products

            # 2. Iterate through each product
            for i, product_data in enumerate(products_to_process):
                product_name = product_data.get('nombrePadre')
                print(f"\n[{i+1}/{len(products_to_process)}] Processing: {product_name}")

                supplier_variants_active = {
                    h['skuHijo']: h for h in product_data.get('hijos', []) if h.get('estatus') == '1'
                }
                if not supplier_variants_active:
                    print(f"  Skipping '{product_name}' - no active variants.")
                    continue

                # 3. Check for existing product in Shopify
                # We check the first active variant's SKU to see if the product exists.
                first_sku = next(iter(supplier_variants_active))
                existing_product_info = self.shopify_client.find_product_variant_by_sku(first_sku)

                if not existing_product_info:
                    # 4a. CREATE new product
                    print(f"  Product not found in Shopify. Creating '{product_name}'...")
                    self.shopify_client.create_product(product_data)
                else:
                    # 4b. UPDATE existing product
                    print(f"  Product found in Shopify (ID: {existing_product_info['product_id']}). Checking for updates...")
                    shopify_variants = self.shopify_client.get_variants_for_product(existing_product_info['product_id'])
                    shopify_variants_by_sku = {v.sku: v for v in shopify_variants}

                    # Check for price updates on existing variants
                    for sku, supplier_variant in supplier_variants_active.items():
                        if sku in shopify_variants_by_sku:
                            shopify_variant = shopify_variants_by_sku[sku]

                            # Calculate new price
                            try:
                                base_price = float(supplier_variant.get('precio', 0))
                                new_price = (base_price * 0.77) / 0.60
                            except (ValueError, TypeError):
                                new_price = 0.0

                            # Compare and update price
                            if abs(float(shopify_variant.price) - new_price) > 0.01:
                                print(f"    - Updating price for SKU {sku}: {shopify_variant.price} -> {new_price:.2f}")
                                self.shopify_client.update_variant_price(shopify_variant.id, new_price)

                    # Check for variants to delete
                    supplier_skus = set(supplier_variants_active.keys())
                    shopify_skus = set(shopify_variants_by_sku.keys())
                    skus_to_delete = shopify_skus - supplier_skus

                    for sku in skus_to_delete:
                        variant_to_delete = shopify_variants_by_sku[sku]
                        print(f"    - Deleting discontinued variant SKU {sku} (ID: {variant_to_delete.id})")
                        self.shopify_client.delete_product_variant(variant_to_delete.product_id, variant_to_delete.id)

        except Exception as e:
            print(f"A critical error occurred during the sync process: {e}")
        finally:
            self.shopify_client.close_session()
            print("\n--- Full Product Sync Finished ---")


if __name__ == '__main__':
    manager = SyncManager()
    # For the test run, we'll only process the first 5 products from the supplier.
    manager.run_full_sync(product_limit=5)
