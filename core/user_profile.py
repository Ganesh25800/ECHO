class user:
    def __init__(self, **args):
        self.user_id = args.get("user_id")
        self.name = args.get("name")
        self.prefered_name = args.get("prefered_name")
        self.gender = args.get("gender")
        self.age = args.get("age")
        self.date_of_birth = args.get("date_of_birth")
        self.prefered_language = args.get("prefered_language")
        self.time_zone = args.get("time_zone")
        self.user_from = args.get("user_from")

        self.user_interest = args.get("user_interest")
        self.face_embeddings = args.get("face_embeddings")

    def get_user_id(self):
        return self.user_id

    def get_name(self):
        return self.name

    def get_prefered_name(self):
        return self.prefered_name

    def get_gender(self):
        return self.gender

    def get_age(self):
        return self.age

    def get_date_of_birth(self):
        return self.date_of_birth

    def get_prefered_language(self):
        return self.prefered_language

    def get_user_interest(self):
        return self.user_interest

    def get_embeddings(self):
        return self.face_embeddings    