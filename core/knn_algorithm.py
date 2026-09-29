import numpy as np
from sklearn.neighbors import KNeighborsClassifier

class FaceKNN:

    def __init__(self ,k=5, threshold=0.45):
        self.k = k
        self.threshold = threshold

        self.knn = KNeighborsClassifier(
            n_neighbors=k,
            metric = "cosine",
            weights = "distance"
        )

        self.user_profiles = {}
        self.user_ids = None
        self.training_size = 0
        self.is_trained = False


    def train(self, embeddings, user_ids):

        embeddings = np.asarray(
            embeddings,
            dtype = np.float32
        )

        user_ids = np.asarray(user_ids)

        norms = np.linalg.norm(
            embeddings,
            axis = 1,
            keepdims = True
        )

        norms[norms == 0] = 1.0

        embeddings = embeddings / norms

        self.user_ids = user_ids
        self.training_size = len(embeddings)

        self.knn.fit(
            embeddings,
            user_ids
        )

        self.is_trained = True


    def predict(self, new_embedding):

        if not self.is_trained:
            return None, 0.0

        new_embedding = np.asarray(
            new_embedding,
            dtype = np.float32
        )

        if new_embedding.ndim == 1:
            new_embedding = new_embedding.reshape(1,-1)

        norm = np.linalg.norm(
            new_embedding,
            axis = 1,
            keepdims = True
        )

        valid = norm[:, 0] != 0

        normalized_embeddings = np.zeros_like(new_embedding)

        normalized_embeddings[valid] = new_embedding[valid] / norm[valid]

        k = min(
            self.k,
            self.training_size
        )

        distances, indexes = self.knn.kneighbors(
            normalized_embeddings,
            n_neighbors = k
        )

        predicted_user_ids = self.knn.predict(normalized_embeddings)

        results = []

        for face_index in range(len(normalized_embeddings)):

            if not valid[face_index]:
                results.append(("unknown person", 0.0))
                continue

            predicted_user_id = (predicted_user_ids[face_index])

            neighbor_indexs = (indexes[face_index])

            neighbor_distances = (distances[face_index])

            neighbor_user_ids = (self.user_ids[neighbor_indexs])

            matching_distances = []

            for user_id, distance in zip(neighbor_user_ids, neighbor_distances):

                if user_id == predicted_user_id:
                    matching_distances.append(distance)

            if not matching_distances:
                results.append(("unknown person", 0))
                continue

            average_distance = float(np.mean(matching_distances))

            similarity = (1.0 - average_distance)

            confidence = round(
                max(0.0, min(
                    1.0, similarity
                ))*100, 2
            )

            if similarity < self.threshold:
                results.append(("unknown person",confidence))

            else:
                results.append((predicted_user_id, confidence))


        return results