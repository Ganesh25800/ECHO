from config.database_helper import database
from config.database_query_helper import QueriesHelper as qh
from core.user_profile import user as u
from core.knn_algorithm import FaceKNN


def check_for_user(users,embedding):
    
    all_users_embeddings = []
    user_names_for_embeddings = []

    if not users:
        return "no users found"
    
    for i in users:
        embeddings = i.get_embeddings()
        user_id = i.get_user_id()

        for j in embeddings:
            all_users_embeddings.append(j)
            user_names_for_embeddings.append(user_id)

    if len(all_users_embeddings) == 0:
        print("No embeddings")

    knn = FaceKNN(k=5, threshold = 0.45)

    knn.train(all_users_embeddings, user_names_for_embeddings)

    result = knn.predict(embedding)

    return result




def sort_users(users):

    users = []

    if not users:
        return None

    for user in users:

        user_id = user.get("user_id")
        name = user.get("name")
        prefered_name = user.get("prefered_name")
        age = user.get("age")
        date_of_birth = user.get("date_of_birth")
        prefered_language = user.get("prefered_language")
        time_zone = user.get("time_zone")
        user_from = user.get("user_from")

        user_interests = database.get_all_data_of_user(qh.GET_USER_INTEREST,user_id=user_id)

        user_interest = []

        for i in user_interests:
            user_interest.append(i.get("interest"))

        face_embeddings = []

        user_face_embeddings = database.get_all_data_of_user(qh.GET_USER_FACE_EMBEDDINGS,user_id=user_id)

        for i in user_face_embeddings:
            face_embeddings.append(i.get("embedding"))


        user_ = u(user_id,name,prefered_name,age,date_of_birth,prefered_language,time_zone,user_from,user_interest,face_embeddings)

        users.append(user_)

    return users   


