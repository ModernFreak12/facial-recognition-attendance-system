from app.services.supabase_client import get_supabase
supabase = get_supabase()


data1 = {
    "univ_roll_no": "12200222047",
    "name": "Aayush Chowdhury",
    "department": "IT",
    "email": "it23.aayush.chowdhury@stcet.ac.in",
    "class_roll_no": 10,
    "date_of_birth": "2004-10-13",
    "admission_year": 2022,
    "password": "13102004"
}


res = supabase.table("students").insert(data1).execute()
print(res)