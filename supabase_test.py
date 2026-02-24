from app.services.supabase_client import get_supabase
supabase = get_supabase()


data1 = {
    "univ_roll_no": "12200222047",
    "name": "Aayush Chowdhury",
    "department": "IT",
    "class_roll_no": 10,
    "date_of_birth": "2004-10-13",
    "admission_year": 2022
}

'''
data2 = {
    "univ_roll_no": "12200222022",
    "name": "Ankandeep Pal",
    "department": "IT",
    "class_roll_no": 45,
    "admission_year": 2022
}

data3 = {
    "univ_roll_no": "12200222032",
    "name": "Shruti Roy",
    "department": "IT",
    "class_roll_no": 54,
    "admission_year": 2022
}
'''

res = supabase.table("students").insert(data1).execute()
print(res)

'''
res = supabase.table("students").insert(data2).execute()
print(res)

res = supabase.table("students").insert(data3).execute()
print(res)
'''