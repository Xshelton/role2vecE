import math
import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm
from gensim.models.doc2vec import Doc2Vec
from utils import load_graph, create_documents
from walkers import FirstOrderRandomWalker, SecondOrderRandomWalker
from weisfeiler_lehman_labeling import WeisfeilerLehmanMachine
from motif_count import MotifCounterMachine

class Role2Vec:
    """
    Role2Vec model class.
    """
    def __init__(self, args):
        """
        Role2Vec machine constructor.
        :param args: Arguments object with the model hyperparameters.
        """
        self.args = args
        self.graph = load_graph(args.graph_input)

    def do_walks(self):
        """
        Doing first/second order random walks.
        
        """
        #print('首先进行随机游走')
        print('first, the random walk')
        if self.args.sampling == "second":
            self.sampler = SecondOrderRandomWalker(self.graph, self.args.P, self.args.Q,  self.args.walk_number, self.args.walk_length)
        else:
            self.sampler = FirstOrderRandomWalker(self.graph, self.args.walk_number, self.args.walk_length)
        self.walks = self.sampler.walks
        print(type(self.walks))#这个是个类
        #df=pd.DataFrame(self.walks)
        #df.to_csv('seewalks.csv')减少IO 加快速度
       # print()
        
        del self.sampler

    def create_structural_features(self):
        """
        Extracting structural features.
        """
        if self.args.features == "wl":
            print('structure feaetures are WeisfeilerLehman，degree')

            features = {str(node): str(int(math.log(self.graph.degree(node)+1,self.args.log_base))) for node in self.graph.nodes()}
            machine = WeisfeilerLehmanMachine(self.graph, features, self.args.labeling_iterations)
            machine.do_recursions()
            self.features = machine.extracted_features
            print(type(self.features))
            print(len(self.features))
            dddf=pd.DataFrame(self.features)
            dddf.to_csv('features.csv')
        elif self.args.features == "degree":
            self.features = {str(node): [str(self.graph.degree(node))] for node in self.graph.nodes()}
            print(type(self.features))
            print('structural feature is degree')
            dddf=pd.DataFrame(self.features)
            dddf.to_csv('features_degree.csv')
        else:
            machine = MotifCounterMachine(self.graph, self.args)
            self.features  = machine.create_string_labels()#特征直接是提取了string_label
            print(type(self.features))
            print('structural feature is ，motif')
            #dddf=pd.DataFrame(self.features)
            #ddff=dddf.T
            #ddff.to_csv('features_motif.csv')

    def create_pooled_features(self):
        """
        Pooling the features with the walks
        
        """
        print('Third steps: one creating pooled_features')
        features = {str(node):[] for node in self.graph.nodes()}
        for walk in self.walks:
            for node_index in range(self.args.walk_length-self.args.window_size):
                for j in range(1,self.args.window_size+1):
                    features[str(walk[node_index])].append(self.features[str(walk[node_index+j])])
                    features[str(walk[node_index+j])].append(self.features[str(walk[node_index])])

        features = {node: [feature for feature_elems in feature_set for feature in feature_elems] for node, feature_set in features.items()}
        print('the return type of this function ',type(features))
              
        return features
   

    def create_embedding(self):
        """
        Fitting an embedding.
        """
        print('Third steps: two creating embedding using pooled features to generate context and node embedding')
        document_collections = create_documents(self.pooled_features)#这里产生了一个list非常非常大的list
        print(type(document_collections))
        print(len(document_collections))

        model = Doc2Vec(document_collections,
                        vector_size = self.args.dimensions,
                        window = 0, 
                        min_count = self.args.min_count,
                        alpha = self.args.alpha,
                        dm = 0,
                        min_alpha = self.args.min_alpha,
                        sample = self.args.down_sampling,
                        workers = self.args.workers,
                        epochs = self.args.epochs)
        
        embedding = np.array([model.docvecs[str(node)] for node in self.graph.nodes()])
        print('The ty',type(embedding))
        return embedding

    def learn_embedding(self):
        """
        Pooling the features and learning an embedding.
        """
        self.pooled_features = self.create_pooled_features()
        self.embedding = self.create_embedding()

    def save_embedding(self):
        """
        Function to save the embedding.
        """
        columns = ["id"] + [ "x_" +str(x) for x in range(self.embedding.shape[1])]
        ids = np.array([node for node in self.graph.nodes()]).reshape(-1,1)
        self.embedding = pd.DataFrame(np.concatenate([ids, self.embedding], axis = 1), columns = columns)#保存嵌入
        self.embedding = self.embedding.sort_values(by=['id'])#embedding排序
        self.embedding.to_csv(self.args.output, index = None)
