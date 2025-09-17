import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Initialize session state
if "orders" not in st.session_state:
    st.session_state.orders = []
if "cart" not in st.session_state:
    st.session_state.cart = []

# Load product data
def load_products():
    try:
        df_products = pd.read_excel("data/products.xlsx")
        expected_columns = ["SL", "Product Name", "Product code", "price", "amount"]
        if not all(col in df_products.columns for col in expected_columns):
            st.error("Excel file doesn't have all required columns.")
            return pd.DataFrame(columns=expected_columns)
        return df_products
    except FileNotFoundError:
        st.error("❌ data/products.xlsx file not found. Please check the file path.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

# Main app
def main():
    st.title("📦 Order Management System (Cart Enabled)")

    # Load products
    df_products = load_products()
    if df_products.empty:
        st.stop()

    # Customer information
    st.header("📝 Create New Order")
    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input("Customer Name *")
        customer_phone = st.text_input("Customer Phone Number *")
    with col2:
        customer_address = st.text_area("Customer Address")
        order_date = st.date_input("Order Date", datetime.today())

    # Product search + add to cart
    st.subheader("🔍 Search & Add Products to Cart")
    search_query = st.text_input("Search product by name or code")

    if search_query:
        filtered_products = df_products[
            df_products["Product Name"].str.contains(search_query, case=False, na=False)
            | df_products["Product code"].astype(str).str.contains(search_query, case=False, na=False)
        ]

        if not filtered_products.empty:
            selected_product = st.selectbox(
                "Select a product",
                filtered_products["Product Name"].tolist(),
            )
            product_info = filtered_products[filtered_products["Product Name"] == selected_product].iloc[0]

            quantity = st.number_input(
                f"Quantity for {selected_product}",
                min_value=1,
                value=1,
                key=f"qty_{product_info['Product code']}",
            )

            if st.button("➕ Add to Cart"):
                st.session_state.cart.append(
                    {
                        "SL": product_info["SL"],
                        "Product Name": product_info["Product Name"],
                        "Product code": product_info["Product code"],
                        "price": product_info["price"],
                        "quantity": quantity,
                        "amount": quantity * product_info["price"],
                    }
                )
                st.success(f"{selected_product} added to cart ✅")
        else:
            st.warning("No products found. Try another search keyword.")

    # Show cart
    if st.session_state.cart:
        st.subheader("🛒 Cart")
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(
            cart_df[["Product code", "Product Name", "quantity", "price", "amount"]],
            hide_index=True,
        )
        total_cart_amount = sum(item["amount"] for item in st.session_state.cart)
        st.write(f"**Total Cart Amount: ৳{total_cart_amount:,.2f}**")

    # Submit order
    if st.button("✅ Create Order"):
        if not customer_name or not customer_phone:
            st.error("Please provide customer name and phone number.")
        elif not st.session_state.cart:
            st.error("Please add at least one product to cart.")
        else:
            # Calculate total amount
            total_order_amount = sum(item["amount"] for item in st.session_state.cart)

            # Save order to session state
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            order_data = {
                "order_id": order_id,
                "customer_info": {
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "customer_address": customer_address,
                    "order_date": order_date,
                },
                "items": st.session_state.cart.copy(),
                "total_amount": total_order_amount,
                "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.orders.append(order_data)

            # Clear cart after order
            st.session_state.cart = []

            # Display summary
            st.success(f"Order created successfully! ✅ Order ID: {order_id}")
            st.subheader("📋 Order Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Customer Information:**")
                st.write(f"Name: {customer_name}")
                st.write(f"Phone: {customer_phone}")
                if customer_address:
                    st.write(f"Address: {customer_address}")
                st.write(f"Order Date: {order_date.strftime('%d-%m-%Y')}")
            with col2:
                st.write("**Order Details:**")
                order_df = pd.DataFrame(order_data["items"])
                st.dataframe(order_df[["Product code", "Product Name", "quantity", "price", "amount"]])
                st.write(f"**Total Order Amount: ৳{total_order_amount:,.2f}**")

            # Download option
            st.subheader("⬇️ Download Order")
            customer_data = {
                "customer_name": [customer_name],
                "customer_phone": [customer_phone],
                "customer_address": [customer_address],
                "order_date": [order_date],
                "total_amount": [total_order_amount],
            }
            customer_df = pd.DataFrame(customer_data)
            order_df = pd.DataFrame(order_data["items"])

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                customer_df.to_excel(writer, sheet_name="Customer Info", index=False)
                order_df.to_excel(writer, sheet_name="Order Details", index=False)
            output.seek(0)

            st.download_button(
                label="Download Order as Excel File",
                data=output,
                file_name=f"order_{customer_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Order history
    if st.session_state.orders:
        st.header("📜 Order History")
        for order in reversed(st.session_state.orders):
            with st.expander(
                f"Order {order['order_id']} - {order['customer_info']['customer_name']} - ৳{order['total_amount']:,.2f}"
            ):
                st.write("**Customer Information:**")
                st.write(f"Name: {order['customer_info']['customer_name']}")
                st.write(f"Phone: {order['customer_info']['customer_phone']}")
                if order["customer_info"]["customer_address"]:
                    st.write(f"Address: {order['customer_info']['customer_address']}")
                st.write(f"Order Date: {order['order_date']}")

                st.write("**Order Details:**")
                order_df = pd.DataFrame(order["items"])
                st.dataframe(order_df[["Product code", "Product Name", "quantity", "price", "amount"]])
                st.write(f"**Total Amount: ৳{order['total_amount']:,.2f}**")

                # Download button for this order
                customer_info = order["customer_info"]
                customer_data = {
                    "customer_name": [customer_info["customer_name"]],
                    "customer_phone": [customer_info["customer_phone"]],
                    "customer_address": [customer_info["customer_address"]],
                    "order_date": [order["order_date"]],
                    "total_amount": [order["total_amount"]],
                }
                customer_df = pd.DataFrame(customer_data)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    customer_df.to_excel(writer, sheet_name="Customer Info", index=False)
                    order_df.to_excel(writer, sheet_name="Order Details", index=False)
                output.seek(0)

                st.download_button(
                    label=f"Download Order {order['order_id']}",
                    data=output,
                    file_name=f"order_{order['order_id']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{order['order_id']}",
                )

if __name__ == "__main__":
    main()
