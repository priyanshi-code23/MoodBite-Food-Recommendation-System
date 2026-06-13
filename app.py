import streamlit as st
from db import get_connection
import random 

st.set_page_config(
    page_title="MoodBite",
    page_icon="🍔",
    layout="wide"
)

# Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""    
if "cart_message" not in st.session_state:
    st.session_state.cart_message = ""
if "order_confirmed" not in st.session_state:
    st.session_state.order_confirmed = False    
if "show_recommendations" not in st.session_state:
    st.session_state.show_recommendations = False    
# LOGIN SCREEN
if not st.session_state.logged_in:

    st.title("🍔 MoodBite")
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT name
                FROM users
                WHERE email = %s AND password = %s
                """,
                (email, password)
            )

            user = cur.fetchone()

            cur.close()
            conn.close()

            if user:
                st.session_state.logged_in = True
                st.session_state.user_name = user[0]
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("❌ Invalid Email or Password")

        except Exception as e:
            st.error(f"❌ Error: {e}")

# DASHBOARD SCREEN
else:

    st.sidebar.title("🍔 MoodBite")
    st.sidebar.write(f"👤 {st.session_state.user_name}")

    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Food Menu", "Cart", "Orders", "Recommendations","Wishlist"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.rerun()

    # Home
    if page == "Home":
        st.title("🏠 Home")
        st.success(f"Welcome, {st.session_state.user_name}! 🎉")
        st.write("Welcome to MoodBite!")

    # Food Menu
    elif page == "Food Menu":
        st.title("🍕 Food Menu")
        if st.session_state.get("cart_message"):
            st.success(st.session_state.cart_message)
            st.session_state.cart_message = ""

        # Search Box
        search = st.text_input("🔍 Search Food")

        # Category Filter
        category_filter = st.selectbox(
          "🥗 Category",
          ["All", "Veg", "Non-Veg"]
        )

        # Cuisine Filter
        cuisine_filter = st.selectbox(
          "🍽 Cuisine",
          ["All", "Indian", "Italian", "Chinese", "Fast Food", "Dessert"]
        )

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
               SELECT food_name,
                   cuisine,
                   price,
                   category,
                   rating
               FROM food_items
            """)

            foods = cur.fetchall()

            cur.close()
            conn.close()

            for food in foods:
                # Search Filter
                if search and search.lower() not in food[0].lower():
                    continue

                # Category Filter
                if category_filter != "All" and food[3] != category_filter:
                    continue

                # Cuisine Filter
                if cuisine_filter != "All" and food[1] != cuisine_filter:
                    continue

                st.markdown("---")
                st.subheader(food[0])
                st.write(f"🍽 Cuisine: {food[1]}")
                st.write(f"💰 Price: ₹{food[2]}")
                st.write(f"🥗 Category: {food[3]}")
                st.write(f"⭐ Rating: {food[4]}")

                if st.button(f"Add to Cart - {food[0]}", key=f"cart_{food[0]}"):
                    conn = get_connection()
                    cur = conn.cursor()

                    # Check if item already exists
                    cur.execute(
                       """
                       SELECT quantity
                       FROM cart
                       WHERE user_email = %s
                       AND food_name = %s
                       """,
                       (
                         st.session_state.user_email,
                         food[0]
                       )
                    )

                    existing_item = cur.fetchone()

                    if existing_item:
                        cur.execute(
                           """
                           UPDATE cart
                           SET quantity = quantity + 1
                           WHERE user_email = %s
                           AND food_name = %s
                           """,
                           (
                             st.session_state.user_email,
                             food[0]
                           )
                        )
                    else:
                        cur.execute(
                           """
                           INSERT INTO cart
                           (user_email, food_name, price, quantity)
                           VALUES (%s, %s, %s, %s)
                           """,
                           (
                             st.session_state.user_email,
                             food[0],
                             food[2],
                             1
                           )
                        )

                    conn.commit()

                    cur.close()
                    conn.close()

                    st.session_state.cart_message = "Added to Cart ✅"
                    st.rerun() 

        except Exception as e:
            st.error(f"Error: {e}")
    # Cart
    elif page == "Cart":
        st.title("🛒 Your Cart")
        if st.session_state.order_confirmed:
           st.success("✅ Your Order is Confirmed!")
           st.session_state.order_confirmed = False

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
        """
        SELECT food_name, price,quantity
        FROM cart
        WHERE user_email = %s
        """,
        (st.session_state.user_email,)
    )

        items = cur.fetchall()

        cur.close()
        conn.close()
 
        total = 0

        if items:
            
            for item in items:
                col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 1, 1])

                with col1:
                    st.write(f"🍔 {item[0]}")
                    st.caption(f"₹{item[1]} each")

    # Minus Button
                with col2:
                    if st.button("➖", key=f"minus_{item[0]}"):
                        conn = get_connection()
                        cur = conn.cursor()

                        if item[2]>1:
                            cur.execute(
                               """
                               UPDATE cart
                               SET quantity = quantity - 1
                               WHERE user_email = %s
                               AND food_name = %s
                               """,
                               (
                                 st.session_state.user_email,
                                 item[0]
                               )
                            )
                        else:
                            cur.execute(
                              """
                              DELETE FROM cart
                              WHERE user_email = %s
                              AND food_name = %s
                              """,
                              (
                                st.session_state.user_email,
                                item[0]
                              )
                            )

                        conn.commit()
                        cur.close()
                        conn.close()

                        st.rerun()

    # Quantity Number
                with col3:
                    st.write(f"### {item[2]}")

    # Plus Button
                with col4:
                    if st.button("➕", key=f"plus_{item[0]}"):
                        conn = get_connection()
                        cur = conn.cursor()

                        cur.execute(
                           """
                           UPDATE cart
                           SET quantity = quantity + 1
                           WHERE user_email = %s
                           AND food_name = %s
                           """,
                           (
                             st.session_state.user_email,
                             item[0]
                           )
                        )

                        conn.commit()
                        cur.close()
                        conn.close()

                        st.rerun()

    # Remove Button
                with col5:
                    if st.button("❌", key=f"remove_{item[0]}"):
                        conn = get_connection()
                        cur = conn.cursor()

                        cur.execute(
                           """
                           DELETE FROM cart
                           WHERE user_email = %s
                           AND food_name = %s
                           """,
                           (
                             st.session_state.user_email,
                             item[0]
                            )
                        )

                        conn.commit()
                        cur.close()
                        conn.close()

                        st.rerun()

            total += float(item[1]) * item[2]

            st.markdown("---")

        st.subheader(f"Total: ₹{total}")
              
        if st.button("Checkout"):
            conn = get_connection()
            cur = conn.cursor()

            for item in items:
                cur.execute(
                   """
                   INSERT INTO orders (user_email, food_name, price)
                   VALUES (%s, %s, %s)
                   """,
                   (
                     st.session_state.user_email,
                     item[0],
                     item[1]
                   )
                )

            cur.execute(
                """
                DELETE FROM cart
                WHERE user_email = %s
                """,
                (st.session_state.user_email,)
            )

            conn.commit()
            
            delivery_time = random.randint(20, 45)
            st.session_state.delivery_time = delivery_time
            
            st.session_state.order_confirmed = True

            cur.close()
            conn.close()

            st.success("✅ Your Order is Confirmed!")
            st.balloons()

            st.info(
               f"🚴 Estimated Delivery Time: {delivery_time} mins\n\n"
              "❤️ Thank you for ordering with MoodBite!"
            )

            st.rerun()
        else:
            st.info("Your cart is empty.")
        
    # Orders
    elif page == "Orders":
        
        st.title("📦 Your Orders")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
        """
        SELECT food_name, price, order_date
        FROM orders
        WHERE user_email = %s
        ORDER BY order_date DESC
        """,
        (st.session_state.user_email,)
        )

        orders = cur.fetchall()

        cur.close()
        conn.close()

        if orders:
            
            for order in orders:
                st.markdown("---")
                st.write(f"🍔 Food: {order[0]}")
                st.write(f"💰 Price: ₹{order[1]}")
                st.write(f"📅 Ordered On: {order[2]}")
                st.write("🟢 Status: Confirmed")
                if "delivery_time" in st.session_state:
                    st.write(
                      f"🚴 Estimated Delivery Time: "
                      f"{st.session_state.delivery_time} mins"
                   )
                
        else:
            st.info("You haven't placed any orders yet.")

  # Recommendations
    elif page == "Recommendations":
        st.title("🤖 Mood-Based Recommendations")

        selected_mood = st.selectbox(
          "😊 How are you feeling?",
         ["Happy","Sad","Stressed","Tired",
          "Comfort","Late Night","Party"]
        )
        

        selected_craving = st.selectbox(
          "🍕 What are you craving?",
          ["Healthy", "StreetStyle", "Savory",
          "Creamy", "Crunchy", "Spicy"]
        )
        
        max_price = st.slider(
          "Select your budget (₹)",
          min_value=50,
          max_value=1000,
          value=500,
          step=50
        )
        
        if st.button("Get Recommendations") or st.session_state.get("show_recommendations", False):
            st.session_state.show_recommendations = True  
            
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
            SELECT food_name,cuisine,price,category,rating,calories
            FROM food_items
            WHERE mood_tag = %s
            AND craving_tag = %s
            AND price <= %s
            ORDER BY rating DESC
            LIMIT 5
            """,(selected_mood,selected_craving,max_price)) 

            recommendations = cur.fetchall()

            cur.close()
            conn.close() 

            if recommendations:
                st.success(
                  f"✨ Recommended foods for "
                  f"{selected_mood} mood "
                  f"and {selected_craving} craving:"
                )

                for food in recommendations:
                    st.markdown("---")
                    st.subheader(food[0])
                    st.write(f"🍽 Cuisine: {food[1]}")
                    st.write(f"💰 Price: ₹{food[2]}")
                    st.write(f"🥗 Category: {food[3]}")
                    st.write(f"⭐ Rating: {food[4]}")
                    st.write(f"🔥 Calories: {food[5]} kcal")
                    if st.button(
                       f"Add to Cart - {food[0]}",
                       key=f"rec_cart_{food[0]}"
                    ):
                       
                       conn = get_connection()
                       cur = conn.cursor()

                       cur.execute(
                         """
                         SELECT quantity
                         FROM cart
                         WHERE user_email = %s
                         AND food_name = %s
                         """,
                         (
                           st.session_state.user_email,
                           food[0]
                         )
                       )

                       existing_item = cur.fetchone()

                       if existing_item:
                           cur.execute(
                               """
                               UPDATE cart     
                               SET quantity = quantity + 1
                               WHERE user_email = %s
                               AND food_name = %s
                               """,
                               (
                                 st.session_state.user_email,
                                 food[0]
                               )
                             )

                       else:
                           cur.execute(
                             """
                             INSERT INTO cart
                             (user_email, food_name, price, quantity)
                             VALUES (%s, %s, %s, %s)
                             """,
                            (
                              st.session_state.user_email,
                              food[0],
                              food[2],
                              1
                            )
                          )

                       conn.commit()

                       cur.close()
                       conn.close()

                       st.success("Added to Cart ✅")
                       
                    st.write("❤️ Save button loaded")
                    
                    if st.button(
                        f"❤️ Save - {food[0]}",
                        key=f"fav_{food[0]}"
                    ):
                        conn = get_connection()
                        cur = conn.cursor()

                        cur.execute(
                           """
                           SELECT *
                           FROM favorites
                           WHERE user_email = %s
                           AND food_name = %s
                           """,
                           (
                              st.session_state.user_email,
                              food[0]
                           )
                        )

                        existing = cur.fetchone()

                        if existing:
                            st.info("Already in Wishlist ❤️")

                        else:
                            cur.execute(
                               """
                               INSERT INTO favorites
                               (user_email, food_name, price)
                               VALUES (%s, %s, %s)
                               """,
                               (
                                  st.session_state.user_email,
                                  food[0],
                                  food[2]
                               )
                            )

                            conn.commit()

                            st.success("Added to Wishlist ❤️")

                        cur.close()
                        conn.close()
                       
                    st.caption(
                         f"💡 Recommended because you're feeling "
                         f"{selected_mood} and craving {selected_craving}."
                       )

            else:
                st.info(
                  "No recommendations found. "
                  "Try another mood or craving!"
                )
                
#Wishlist 
    elif page == "Wishlist":
        st.title("❤️ My Wishlist")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
          """
          SELECT food_name, price, added_on
          FROM favorites
          WHERE user_email = %s
          ORDER BY added_on DESC
          """,
          (st.session_state.user_email,)
        )

        favorites = cur.fetchall()

        cur.close()
        conn.close()

        if favorites:
            
            for item in favorites:
                st.markdown("---")

                col1, col2, col3 = st.columns([5, 2, 2])

                with col1:
                    st.write(f"🍔 Food: {item[0]}")
                    st.write(f"💰 Price: ₹{item[1]}")
                    st.write(f"❤️ Saved On: {item[2]}")

                with col2:
                    if st.button("🛒 Add to Cart", key=f"wish_cart_{item[0]}"):
                        
                        conn = get_connection()
                        cur = conn.cursor()

                        cur.execute(
                          """
                          SELECT quantity
                          FROM cart
                          WHERE user_email = %s
                          AND food_name = %s
                          """,
                          (
                            st.session_state.user_email,
                            item[0]
                          )
                       )

                        existing = cur.fetchone()

                        if existing:
                            cur.execute(
                               """
                               UPDATE cart
                               SET quantity = quantity + 1
                               WHERE user_email = %s
                               AND food_name = %s
                               """,
                               (
                                 st.session_state.user_email,
                                 item[0]
                               )
                          )
                        else:
                            cur.execute(
                              """
                              INSERT INTO cart
                              (user_email, food_name, price, quantity)
                              VALUES (%s, %s, %s, %s)
                              """,
                              (
                                st.session_state.user_email,
                                item[0],
                                item[1],
                                1
                              )
                            )

                        conn.commit()
                        cur.close()
                        conn.close()

                        st.success("Added to Cart ✅")
                        st.rerun()

                with col3:
                    if st.button("❌ Remove", key=f"wish_remove_{item[0]}"):
                        
                        conn = get_connection()
                        cur = conn.cursor()

                        cur.execute(
                           """
                           DELETE FROM favorites
                           WHERE user_email = %s
                           AND food_name = %s
                           """,
                           (
                             st.session_state.user_email,
                             item[0]
                           )
                        )

                        conn.commit()
                        cur.close()
                        conn.close()

                        st.success("Removed from Wishlist ❤️")
                        st.rerun()
        else:
            st.info("Your wishlist is empty ❤️")        
            
            