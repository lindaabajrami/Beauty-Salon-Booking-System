from __future__ import annotations

import os
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
STATUS_OPTIONS = ["scheduled", "completed", "cancelled", "no_show"]
CHART_COLORS = ["#0f766e", "#f59e0b", "#6366f1", "#ef4444", "#8b5cf6"]

st.set_page_config(page_title="Bloom Beauty", page_icon="BB", layout="wide")


def api_request(method: str, path: str, api_key: str = "", payload: dict | None = None, params: dict | None = None):
    headers = {"api-key": api_key} if api_key else {}
    try:
        response = requests.request(
            method,
            f"{BASE_URL}{path}",
            json=payload,
            params=params,
            headers=headers,
            timeout=8,
        )
    except requests.RequestException as exc:
        st.error(f"API connection failed: {exc}")
        return None

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        st.error(f"{response.status_code}: {detail}")
        return None

    return response.json() if response.content else {}


def get_list(path: str) -> list[dict]:
    data = api_request("GET", path)
    return data if isinstance(data, list) else []


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def parse_date(value: str | None) -> date:
    try:
        return date.fromisoformat(value or "")
    except ValueError:
        return date.today()


def parse_time(value: str | None) -> time:
    try:
        return datetime.strptime(value or "09:00", "%H:%M").time()
    except ValueError:
        return time(9, 0)


def label_map(items: list[dict], label_field: str) -> dict[str, int]:
    return {f"{item['id']} - {item[label_field]}": item["id"] for item in items}


def show_table(data: list[dict], empty_message: str) -> pd.DataFrame:
    df = pd.DataFrame(data)
    if df.empty:
        st.info(empty_message)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
    return df


def require_admin(api_key: str) -> bool:
    if api_key:
        return True
    st.warning("Admin API key required for this action.")
    return False


def init_session() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("admin_key", "")


def auth_screen() -> None:
    st.title("Bloom Beauty")
    st.subheader("Sign in or create an account")

    tab_login, tab_signup = st.tabs(["Sign in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", value=os.getenv("SEEDED_USER_EMAIL", "mira@example.com"))
            password = st.text_input("Password", type="password", value=os.getenv("SEEDED_USER_PASSWORD", ""))
            submitted = st.form_submit_button("Sign in")

        if submitted:
            response = api_request("POST", "/auth/login", payload={"email": email, "password": password})
            if response:
                st.session_state.user = response["user"]
                st.success("Signed in.")
                rerun()

    with tab_signup:
        with st.form("signup_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email", key="signup_email")
            phone = st.text_input("Phone")
            password = st.text_input("Password", type="password", key="signup_password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            payload = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "password": password,
            }
            response = api_request("POST", "/auth/signup", payload=payload)
            if response:
                st.session_state.user = response["user"]
                st.success("Account created.")
                rerun()


def sidebar_navigation() -> str:
    user = st.session_state.user
    with st.sidebar:
        st.title("Bloom Beauty")
        st.write(f"Signed in as {user['full_name']}")
        st.session_state.admin_key = st.text_input(
            "Admin key",
            type="password",
            value=st.session_state.admin_key,
        )
        st.caption("Needed only for admin CRUD actions.")
        page = st.radio(
            "Navigation",
            ["Dashboard", "Services", "Appointments", "Customers", "Staff", "Profile", "Admin"],
        )
        if st.button("Sign out"):
            st.session_state.user = None
            rerun()
        st.caption(f"API: {BASE_URL}")
    return page


def dashboard_page(api_key: str) -> None:
    current_user = st.session_state.user
    appointments = get_list("/appointments/")
    services = get_list("/services/")

    if api_key:
        st.title("Dashboard")
        summary = api_request("GET", "/admin/summary") or {}
        customers = get_list("/customers/")
        staff = get_list("/staff/")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Customers", summary.get("customers", len(customers)))
        col2.metric("Appointments", summary.get("appointments", len(appointments)))
        col3.metric("Upcoming", summary.get("upcoming_appointments", 0))
        col4.metric("Revenue", f"${summary.get('estimated_revenue', 0):,.0f}")
    else:
        st.title("My Dashboard")
        appointments = [
            appointment for appointment in appointments
            if appointment["customer_id"] == current_user["id"]
        ]
        upcoming_count = len([
            appointment for appointment in appointments
            if appointment["status"] == "scheduled"
        ])
        completed_count = len([
            appointment for appointment in appointments
            if appointment["status"] == "completed"
        ])
        col1, col2, col3 = st.columns(3)
        col1.metric("My appointments", len(appointments))
        col2.metric("Upcoming", upcoming_count)
        col3.metric("Available services", len([item for item in services if item.get("active")]))

    df_appointments = pd.DataFrame(appointments)
    left, right = st.columns(2)

    with left:
        st.subheader("Appointments by status")
        if not df_appointments.empty:
            status_counts = df_appointments["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig = px.pie(
                status_counts,
                names="status",
                values="count",
                hole=0.45,
                color_discrete_sequence=CHART_COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointments yet.")

    with right:
        st.subheader("Revenue by service")
        if not df_appointments.empty:
            completed = df_appointments[df_appointments["status"] == "completed"]
            revenue = completed.groupby("service_name", as_index=False)["price"].sum()
            fig = px.bar(
                revenue,
                x="service_name",
                y="price",
                color="service_name",
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Revenue")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completed appointments yet.")

    st.subheader("Booking calendar")
    if not df_appointments.empty:
        daily = df_appointments.groupby("appointment_date", as_index=False).size()
        daily.columns = ["appointment_date", "count"]
        fig = px.line(daily, x="appointment_date", y="count", markers=True)
        fig.update_traces(line_color="#0f766e", marker_color="#f59e0b")
        fig.update_layout(xaxis_title="", yaxis_title="Bookings")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No booking trend available.")

    if api_key:
        staff = get_list("/staff/")
        c1, c2, c3 = st.columns(3)
        c1.metric("Active services", len([item for item in services if item.get("active")]))
        c2.metric("Active staff", len([item for item in staff if item.get("active")]))
        c3.metric("Avg service price", f"${pd.DataFrame(services)['price'].mean():.0f}" if services else "$0")
    else:
        st.info("Enter the admin key in the sidebar to see full salon business metrics.")


def services_page(api_key: str) -> None:
    st.title("Services")
    services = get_list("/services/")

    if services:
        cols = st.columns(3)
        for index, service in enumerate(services):
            with cols[index % 3]:
                image_path = PROJECT_DIR / service.get("image_path", "")
                if image_path.exists():
                    st.image(str(image_path), use_container_width=True)
                st.subheader(service["name"])
                st.write(service["category"])
                st.write(f"{service['duration_minutes']} minutes")
                st.write(f"${service['price']:.2f}")
    else:
        st.info("No services found.")

    st.divider()
    show_table(services, "No services found.")

    with st.form("create_service"):
        st.subheader("Create service")
        name = st.text_input("Name")
        category = st.text_input("Category")
        duration = st.number_input("Duration minutes", min_value=5, max_value=480, value=60, step=5)
        price = st.number_input("Price", min_value=0.0, value=50.0, step=5.0)
        image_path = st.text_input("Image path", value="assets/services/signature_facial.png")
        active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Create")

    if submitted and require_admin(api_key):
        payload = {
            "name": name,
            "category": category,
            "duration_minutes": int(duration),
            "price": float(price),
            "active": active,
            "image_path": image_path,
        }
        if api_request("POST", "/services/", api_key, payload):
            st.success("Service created.")
            rerun()

    if services:
        st.subheader("Update or delete service")
        options = {f"{item['id']} - {item['name']}": item for item in services}
        selected_label = st.selectbox("Select service", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_service"):
            name = st.text_input("Name", value=selected["name"], key="service_name_update")
            category = st.text_input("Category", value=selected["category"], key="service_category_update")
            duration = st.number_input(
                "Duration minutes",
                min_value=5,
                max_value=480,
                value=int(selected["duration_minutes"]),
                step=5,
                key="service_duration_update",
            )
            price = st.number_input(
                "Price",
                min_value=0.0,
                value=float(selected["price"]),
                step=5.0,
                key="service_price_update",
            )
            image_path = st.text_input("Image path", value=selected.get("image_path", ""), key="service_image_update")
            active = st.checkbox("Active", value=bool(selected["active"]), key="service_active_update")
            update_clicked = st.form_submit_button("Update")

        delete_clicked = st.button("Delete selected service")

        if update_clicked and require_admin(api_key):
            payload = {
                "name": name,
                "category": category,
                "duration_minutes": int(duration),
                "price": float(price),
                "active": active,
                "image_path": image_path,
            }
            if api_request("PUT", f"/services/{selected['id']}", api_key, payload):
                st.success("Service updated.")
                rerun()

        if delete_clicked and require_admin(api_key):
            if api_request("DELETE", f"/services/{selected['id']}", api_key):
                st.success("Service deleted.")
                rerun()


def appointments_page(api_key: str) -> None:
    st.title("Appointments")
    appointments = get_list("/appointments/")
    if not api_key:
        appointments = [
            appointment for appointment in appointments
            if appointment["customer_id"] == st.session_state.user["id"]
        ]
    customers = get_list("/customers/")
    services = get_list("/services/?active_only=true")
    staff = get_list("/staff/?active_only=true")

    df = show_table(appointments, "No appointments found.")
    customer_options = label_map(customers, "full_name")
    service_options = label_map(services, "name")
    staff_options = label_map(staff, "full_name")

    st.subheader("Create appointment")
    if customer_options and service_options and staff_options:
        with st.form("create_appointment"):
            current_user = st.session_state.user
            if api_key:
                default_customer = next(
                    (label for label, customer_id in customer_options.items() if customer_id == current_user["id"]),
                    list(customer_options.keys())[0],
                )
                customer_label = st.selectbox(
                    "Customer",
                    list(customer_options.keys()),
                    index=list(customer_options.keys()).index(default_customer),
                )
                customer_id = customer_options[customer_label]
            else:
                st.write(f"Customer: {current_user['full_name']}")
                customer_id = current_user["id"]
            service_label = st.selectbox("Service", list(service_options.keys()))
            staff_label = st.selectbox("Staff", list(staff_options.keys()))
            appointment_day = st.date_input("Date", value=date.today())
            appointment_clock = st.time_input("Time", value=time(10, 0), step=900)
            status_value = "scheduled"
            if api_key:
                status_value = st.selectbox("Status", STATUS_OPTIONS)
            notes = st.text_area("Notes", height=90)
            submitted = st.form_submit_button("Create")

        if submitted:
            payload = {
                "customer_id": customer_id,
                "service_id": service_options[service_label],
                "staff_id": staff_options[staff_label],
                "appointment_date": appointment_day.isoformat(),
                "appointment_time": appointment_clock.strftime("%H:%M"),
                "status": status_value,
                "notes": notes,
            }
            if api_request("POST", "/appointments/", api_key, payload):
                st.success("Appointment created.")
                rerun()

    if not df.empty:
        st.subheader("Update or delete appointment")
        appointment_options = {
            f"{row['id']} - {row['customer_name']} - {row['appointment_date']} {row['appointment_time']}": row
            for row in appointments
        }
        selected_label = st.selectbox("Select appointment", list(appointment_options.keys()))
        selected = appointment_options[selected_label]

        with st.form("update_appointment"):
            customer_labels = list(customer_options.keys())
            service_labels = list(service_options.keys())
            staff_labels = list(staff_options.keys())
            customer_default = next((i for i, label in enumerate(customer_labels) if customer_options[label] == selected["customer_id"]), 0)
            service_default = next((i for i, label in enumerate(service_labels) if service_options[label] == selected["service_id"]), 0)
            staff_default = next((i for i, label in enumerate(staff_labels) if staff_options[label] == selected["staff_id"]), 0)
            customer_label = st.selectbox("Customer", customer_labels, index=customer_default, key="update_customer")
            service_label = st.selectbox("Service", service_labels, index=service_default, key="update_service")
            staff_label = st.selectbox("Staff", staff_labels, index=staff_default, key="update_staff")
            appointment_day = st.date_input("Date", value=parse_date(selected["appointment_date"]), key="update_date")
            appointment_clock = st.time_input("Time", value=parse_time(selected["appointment_time"]), step=900, key="update_time")
            status_value = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(selected["status"]))
            notes = st.text_area("Notes", value=selected.get("notes", ""), height=90, key="update_notes")
            update_clicked = st.form_submit_button("Update")

        delete_clicked = st.button("Delete selected appointment")

        if update_clicked and require_admin(api_key):
            payload = {
                "customer_id": customer_options[customer_label],
                "service_id": service_options[service_label],
                "staff_id": staff_options[staff_label],
                "appointment_date": appointment_day.isoformat(),
                "appointment_time": appointment_clock.strftime("%H:%M"),
                "status": status_value,
                "notes": notes,
            }
            if api_request("PUT", f"/appointments/{selected['id']}", api_key, payload):
                st.success("Appointment updated.")
                rerun()

        if delete_clicked and require_admin(api_key):
            if api_request("DELETE", f"/appointments/{selected['id']}", api_key):
                st.success("Appointment deleted.")
                rerun()


def customers_page(api_key: str) -> None:
    st.title("Customers")
    if not api_key:
        st.warning("Admin key required to manage customers.")
        return
    customers = get_list("/customers/")
    df = show_table(customers, "No customers found.")

    with st.form("create_customer"):
        st.subheader("Create customer")
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Create")

    if submitted and require_admin(api_key):
        payload = {"full_name": full_name, "email": email, "phone": phone, "password": password}
        if api_request("POST", "/customers/", api_key, payload):
            st.success("Customer created.")
            rerun()

    if not df.empty:
        st.subheader("Update or delete customer")
        options = {f"{item['id']} - {item['full_name']}": item for item in customers}
        selected_label = st.selectbox("Select customer", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_customer"):
            full_name = st.text_input("Full name", value=selected["full_name"], key="customer_name_update")
            email = st.text_input("Email", value=selected["email"], key="customer_email_update")
            phone = st.text_input("Phone", value=selected["phone"], key="customer_phone_update")
            password = st.text_input("New password optional", type="password", key="customer_password_update")
            update_clicked = st.form_submit_button("Update")

        delete_clicked = st.button("Delete selected customer")

        if update_clicked and require_admin(api_key):
            payload = {"full_name": full_name, "email": email, "phone": phone}
            if password:
                payload["password"] = password
            if api_request("PUT", f"/customers/{selected['id']}", api_key, payload):
                st.success("Customer updated.")
                rerun()

        if delete_clicked and require_admin(api_key):
            if api_request("DELETE", f"/customers/{selected['id']}", api_key):
                st.success("Customer deleted.")
                rerun()


def staff_page(api_key: str) -> None:
    st.title("Staff")
    if not api_key:
        st.warning("Admin key required to manage staff.")
        return
    staff = get_list("/staff/")
    df = show_table(staff, "No staff found.")

    with st.form("create_staff"):
        st.subheader("Create staff member")
        full_name = st.text_input("Full name")
        specialty = st.text_input("Specialty")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Create")

    if submitted and require_admin(api_key):
        payload = {
            "full_name": full_name,
            "specialty": specialty,
            "email": email,
            "phone": phone,
            "active": active,
        }
        if api_request("POST", "/staff/", api_key, payload):
            st.success("Staff member created.")
            rerun()

    if not df.empty:
        st.subheader("Update or delete staff")
        options = {f"{item['id']} - {item['full_name']}": item for item in staff}
        selected_label = st.selectbox("Select staff member", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_staff_member"):
            full_name = st.text_input("Full name", value=selected["full_name"], key="staff_name_update")
            specialty = st.text_input("Specialty", value=selected["specialty"], key="staff_specialty_update")
            email = st.text_input("Email", value=selected["email"], key="staff_email_update")
            phone = st.text_input("Phone", value=selected["phone"], key="staff_phone_update")
            active = st.checkbox("Active", value=bool(selected["active"]), key="staff_active_update")
            update_clicked = st.form_submit_button("Update")

        delete_clicked = st.button("Delete selected staff member")

        if update_clicked and require_admin(api_key):
            payload = {
                "full_name": full_name,
                "specialty": specialty,
                "email": email,
                "phone": phone,
                "active": active,
            }
            if api_request("PUT", f"/staff/{selected['id']}", api_key, payload):
                st.success("Staff member updated.")
                rerun()

        if delete_clicked and require_admin(api_key):
            if api_request("DELETE", f"/staff/{selected['id']}", api_key):
                st.success("Staff member deleted.")
                rerun()


def profile_page() -> None:
    st.title("Profile")
    user = st.session_state.user
    st.write(f"Customer ID: {user['id']}")

    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=user["full_name"])
        email = st.text_input("Email", value=user["email"])
        phone = st.text_input("Phone", value=user["phone"])
        password = st.text_input("New password optional", type="password")
        submitted = st.form_submit_button("Save profile")

    if submitted:
        payload = {"full_name": full_name, "email": email, "phone": phone}
        if password:
            payload["password"] = password
        response = api_request("PUT", f"/auth/profile/{user['id']}", payload=payload)
        if response:
            st.session_state.user = response["user"]
            st.success("Profile updated.")
            rerun()


def admin_page(api_key: str) -> None:
    st.title("Admin")
    validation = api_request("GET", "/validate_key/", api_key)
    if not validation:
        st.warning("Enter the admin API key in the sidebar.")
        return

    st.success(validation["message"])
    settings = api_request("GET", "/admin/settings", api_key)
    if settings:
        st.json(settings)

    users = api_request("GET", "/admin/users", api_key)
    users = users if isinstance(users, list) else []
    df = show_table(users, "No admin users found.")

    with st.form("create_admin_user"):
        st.subheader("Create admin user")
        username = st.text_input("Username")
        email = st.text_input("Email", key="admin_email_create")
        password = st.text_input("Password", type="password")
        role = st.text_input("Role", value="admin")
        active = st.checkbox("Active", value=True, key="admin_active_create")
        submitted = st.form_submit_button("Create")

    if submitted:
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "active": active,
        }
        if api_request("POST", "/admin/users", api_key, payload):
            st.success("Admin user created.")
            rerun()

    if not df.empty:
        st.subheader("Update or delete admin user")
        options = {f"{item['id']} - {item['username']}": item for item in users}
        selected_label = st.selectbox("Select admin user", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_admin_user"):
            username = st.text_input("Username", value=selected["username"], key="admin_username_update")
            email = st.text_input("Email", value=selected["email"], key="admin_email_update")
            password = st.text_input("New password", type="password", value="changeme")
            role = st.text_input("Role", value=selected["role"], key="admin_role_update")
            active = st.checkbox("Active", value=bool(selected["active"]), key="admin_active_update")
            update_clicked = st.form_submit_button("Update")

        delete_clicked = st.button("Delete selected admin user")

        if update_clicked:
            payload = {
                "username": username,
                "email": email,
                "password": password,
                "role": role,
                "active": active,
            }
            if api_request("PUT", f"/admin/users/{selected['id']}", api_key, payload):
                st.success("Admin user updated.")
                rerun()

        if delete_clicked:
            if api_request("DELETE", f"/admin/users/{selected['id']}", api_key):
                st.success("Admin user deleted.")
                rerun()


init_session()
if st.session_state.user is None:
    auth_screen()
else:
    selected_page = sidebar_navigation()
    admin_key = st.session_state.admin_key
    if selected_page == "Dashboard":
        dashboard_page(admin_key)
    elif selected_page == "Services":
        services_page(admin_key)
    elif selected_page == "Appointments":
        appointments_page(admin_key)
    elif selected_page == "Customers":
        customers_page(admin_key)
    elif selected_page == "Staff":
        staff_page(admin_key)
    elif selected_page == "Profile":
        profile_page()
    elif selected_page == "Admin":
        admin_page(admin_key)
