from scipy import spatial
import itertools

class DuplicateCluster(object):
        
    def __init__(self, index_image_path):
        self.index_image_path = index_image_path
        self.similar_images = []
    
    def appendImagePath(self, imagePath):
        self.similar_images.append(imagePath)
        
def check_if_picture_in_other_cluster(list_of_clusters, image_filepath):
    entry_exists = False
    for cluster in list_of_clusters:
        if image_filepath in cluster.similar_images or image_filepath == cluster.index_image_path:
            entry_exists = True
    return entry_exists

def get_vector_for_filename(dataframe, filename):
    return dataframe.loc[dataframe.image_filename == filename, "vector"].values

def get_similarities_for_filenames(dataframe, filenames):
    similarities = []
    for combinations in itertools.combinations(filenames, 2):
        similarity_dict = {}
        
        vector_1 = get_vector_for_filename(dataframe, combinations[0])[0]
        vector_2 = get_vector_for_filename(dataframe, combinations[1])[0]
        similarity = 1 - spatial.distance.cosine(vector_1, vector_2)
        
        rounded_similarity = int((similarity * 10000)) / 10000.0
        
        if rounded_similarity >= 0.8:
            similarity_dict = {"image_1" : combinations[0],
                               "image_2" : combinations[1],
                               "similarity" : rounded_similarity}

            similarities.append(similarity_dict.copy())
        
    return similarities


def add_image_to_existing_cluster(cluster_list, filepath, initial_results):
    reference_cluster = None
    rounded_similarity = 0.0
    for cluster in cluster_list:
        vector_1 = get_vector_for_filename(initial_results, cluster.index_image_path)[0]
        vector_2 = get_vector_for_filename(initial_results, filepath)[0]
        
        similarity = 1 - spatial.distance.cosine(vector_1, vector_2)
        
        temp_rounded_similarity = int((similarity * 10000)) / 10000.0
        
        if temp_rounded_similarity >= rounded_similarity:
            rounded_similarity = temp_rounded_similarity
            reference_cluster = cluster
    if rounded_similarity >= 0.8:
        reference_cluster.appendImagePath(filepath)

def create_image_clusters(duplicates_dataframe, initial_results):
    cluster_list = []
    for row in duplicates_dataframe.iterrows():
        image_path_exists_as_index = False

        filepath_image_a = row[1]["image_1"]
        filepath_image_b = row[1]["image_2"]
        
        # Case: first iteratrion
        if len(cluster_list) == 0:
            cluster_to_add = DuplicateCluster(filepath_image_a)
            cluster_to_add.appendImagePath(filepath_image_b)
            cluster_list.append(cluster_to_add)
        
        # Case: following iterations
        else:
            if check_if_picture_in_other_cluster(cluster_list, filepath_image_a) == False:       
                if check_if_picture_in_other_cluster(cluster_list, filepath_image_b) == False:
                    cluster_to_add = DuplicateCluster(filepath_image_a)
                    cluster_to_add.appendImagePath(filepath_image_b)
                    cluster_list.append(cluster_to_add)
                else:
                    add_image_to_existing_cluster(cluster_list, filepath_image_a, initial_results)
            else:
                if check_if_picture_in_other_cluster(cluster_list, filepath_image_b) == False:
                    add_image_to_existing_cluster(cluster_list, filepath_image_b, initial_results)
                else:
                    continue
            
    return cluster_list