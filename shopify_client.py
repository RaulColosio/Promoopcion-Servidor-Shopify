import os
import shopify
import time
import json

class ShopifyClient:
    """
    A client to interact with the Shopify API.
    """

    def __init__(self, shop_url, api_token, api_version='2024-04'):
        """
        Initializes the client and activates the Shopify API session.
        :param shop_url: The .myshopify.com URL of the store.
        :param api_token: The Admin API access token.
        :param api_version: The Shopify API version to use.
        """
        if not shop_url or not api_token:
            raise ValueError("Shop URL and API token cannot be empty.")

        session = shopify.Session(shop_url, api_version, api_token)
        shopify.ShopifyResource.activate_session(session)
        print("Shopify session activated.")

    def find_product_variant_by_sku(self, sku):
        """
        Finds a product variant by its SKU using a GraphQL query.
        This is the most efficient way to check if a product exists.
        Returns the variant ID and product ID if found, otherwise None.
        """
        query = """
        query ($sku: String!) {
          productVariants(first: 1, query: "sku:" + $sku) {
            edges {
              node {
                id
                price
                product {
                  id
                }
              }
            }
          }
        }
        """
        variables = {"sku": sku}

        try:
            time.sleep(1)
            result = shopify.GraphQL().execute(query, variables=variables)
            data = json.loads(result)
            variants = data.get('data', {}).get('productVariants', {}).get('edges', [])

            if variants:
                variant_node = variants[0]['node']
                # Return numeric IDs for consistency with REST API objects
                numeric_variant_id = variant_node['id'].split('/')[-1]
                numeric_product_id = variant_node['product']['id'].split('/')[-1]
                price = variant_node['price']
                print(f"Found variant for SKU {sku}. Price: {price}")
                return {
                    "variant_id": numeric_variant_id,
                    "product_id": numeric_product_id,
                    "price": price
                }
            else:
                print(f"No product variant found for SKU: {sku}")
                return None

        except Exception as e:
            print(f"An error occurred during GraphQL request for SKU {sku}: {e}")
            raise

    def update_variant_price(self, numeric_variant_id, new_price):
        """
        Updates the price of a specific product variant.
        :param numeric_variant_id: The numeric ID of the variant.
        :param new_price: The new price to set.
        """
        try:
            variant = shopify.Variant.find(numeric_variant_id)
            variant.price = f"{new_price:.2f}"
            if variant.save():
                print(f"Successfully updated price for variant {numeric_variant_id} to {variant.price}")
                return True
            else:
                print(f"Failed to update price for variant {numeric_variant_id}. Errors: {variant.errors.full_messages()}")
                return False
        except Exception as e:
            print(f"An exception occurred while updating variant {numeric_variant_id}: {e}")
            return False

    def get_variants_for_product(self, numeric_product_id):
        """
        Retrieves all variants for a given product ID.
        :param numeric_product_id: The numeric ID of the product.
        :return: A list of variant objects.
        """
        try:
            product = shopify.Product.find(numeric_product_id)
            return product.variants
        except Exception as e:
            print(f"An exception occurred while fetching variants for product {numeric_product_id}: {e}")
            return []

    def delete_product_variant(self, numeric_product_id, numeric_variant_id):
        """
        Deletes a specific variant from a product.
        :param numeric_product_id: The numeric ID of the parent product.
        :param numeric_variant_id: The numeric ID of the variant to delete.
        """
        try:
            shopify.Variant.delete(numeric_variant_id, product_id=numeric_product_id)
            print(f"Successfully deleted variant {numeric_variant_id} from product {numeric_product_id}")
            return True
        except Exception as e:
            print(f"An exception occurred while deleting variant {numeric_variant_id}: {e}")
            return False

    def create_product(self, product_data):
        """
        Creates a new product in Shopify from the supplier's data format.
        :param product_data: A dictionary for a single product from PromoOptionClient.
        """
        print(f"Preparing to create product: {product_data.get('nombrePadre')}")

        new_product = shopify.Product()
        new_product.title = product_data.get('nombrePadre')
        new_product.body_html = product_data.get('descripcion')
        new_product.vendor = "PromoOpción"
        new_product.product_type = product_data.get('subCategorias', 'General')
        new_product.tags = [product_data.get('categorias'), product_data.get('subCategorias')]

        variants = []
        for hijo in product_data.get('hijos', []):
            try:
                base_price = float(hijo.get('precio', 0))
                # Apply the defined pricing formula
                special_price = base_price * 0.77  # 23% discount
                final_price = special_price / 0.60 # 40% margin on sale price
            except (ValueError, TypeError):
                final_price = 0.0

            # The ShopifyAPI library expects Variant objects, not dicts.
            variant = shopify.Variant()
            variant.option1 = hijo.get('color')
            variant.price = f"{final_price:.2f}"
            variant.sku = hijo.get('skuHijo')
            variant.inventory_management = 'shopify'
            variant.inventory_quantity = 0

            variants.append(variant)

        new_product.variants = variants

        # For images, the library is more flexible and can often accept dicts.
        images = []
        for img_url in product_data.get('imagenesPadre', []):
            images.append({'src': img_url})
        # Also add variant-specific images if available
        for hijo in product_data.get('hijos', []):
            for img_url in hijo.get('imagenesHijo', []):
                images.append({'src': img_url})

        # Remove duplicate images
        unique_images = [dict(t) for t in {tuple(d.items()) for d in images}]
        new_product.images = unique_images

        try:
            if new_product.save():
                print(f"Successfully created product: {new_product.title} (ID: {new_product.id})")
                return new_product.to_dict()
            else:
                # This path is taken if save() returns False
                error_messages = new_product.errors.full_messages()
                print(f"Failed to create product '{new_product.title}'. Errors: {error_messages}")
                return None
        except Exception as e:
            print(f"An exception occurred while saving product '{new_product.title}': {e}")
            return None

    def close_session(self):
        """
        Deactivates the Shopify session.
        """
        shopify.ShopifyResource.clear_session()
        print("Shopify session closed.")


if __name__ == '__main__':
    print("--- Testing ShopifyClient: Create and Update ---")

    shopify_domain = "promotienda-mx.myshopify.com"
    shopify_token = "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"

    if not shopify_domain or not shopify_token:
        print("Error: Shopify domain and token must be available for testing.")
        exit()

    client = None
    try:
        client = ShopifyClient(shop_url=shopify_domain, api_token=shopify_token)

        sample_product_data = {
            "skuPadre": "TSR-041", "nombrePadre": "VASO KIRA (Test)", "categorias": "BEBIDAS",
            "subCategorias": "VASOS", "descripcion": "Vaso de plástico de doble pared con glitter.",
            "hijos": [{"skuHijo": "TSR-041-PLATA", "precio": "100.00", "color": "PLATA"}]
        }
        test_sku = "TSR-041-PLATA"

        # 1. Ensure product exists, using a reliable method
        print(f"\n[1] Finding or Creating test product with SKU: {test_sku}")
        variant_info = client.find_product_variant_by_sku(test_sku)

        if not variant_info:
            print(f"SKU not found. Creating product...")
            created_product = client.create_product(sample_product_data)
            if not created_product or not created_product.get('variants'):
                raise Exception("Failed to create product or product has no variants in response.")

            # Use data directly from the creation response to avoid search indexing delays
            variant = created_product['variants'][0]
            variant_info = {
                "variant_id": variant['id'],
                "product_id": created_product['id'], # Get product_id from the parent object
                "price": variant['price']
            }
            print(f"Product created. Using new variant ID: {variant_info['variant_id']}")
        else:
            print(f"Product found. Using existing variant ID: {variant_info['variant_id']}")

        # 2. Test Price Update
        numeric_variant_id = variant_info['variant_id']
        current_price = float(variant_info['price'])
        new_price = current_price + 1.0

        print(f"\n[2] Updating price for variant ID {numeric_variant_id} from {current_price} to {new_price}")
        update_success = client.update_variant_price(numeric_variant_id, new_price)
        if not update_success:
            raise Exception("Update price method failed.")

        # 3. Verify Price Update via direct lookup (more reliable than search)
        print("\n[3] Verifying price update...")
        time.sleep(1) # Brief wait for changes to settle
        variant_check = shopify.Variant.find(numeric_variant_id)

        if variant_check and abs(float(variant_check.price) - new_price) < 0.001:
            print(f"SUCCESS: Price correctly updated to {variant_check.price}")
        else:
            raise Exception(f"Price update verification failed. Expected {new_price}, found {variant_check.price if variant_check else 'None'}")

        # 4. Cleanup / Revert price
        print(f"\n[4] Reverting price for variant ID {numeric_variant_id} to {current_price}")
        client.update_variant_price(numeric_variant_id, current_price)

        print("\n--- ShopifyClient tests passed! ---")

    except Exception as e:
        print(f"An error occurred during ShopifyClient testing: {e}")
    finally:
        if client:
            client.close_session()
