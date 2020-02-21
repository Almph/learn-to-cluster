import os
import glob
import numpy as np

from utils import (read_meta, read_probs, l2norm, intdict2ndarray, Timer)


class ClusterDataset(object):
    def __init__(self, cfg, is_test=False):
        feat_path = cfg['feat_path']
        label_path = cfg.get('label_path', None)
        proposal_folders = cfg['proposal_folders']

        self.feature_dim = cfg['feature_dim']
        self.featureless = cfg.get('featureless', False)
        self.is_norm_adj = cfg.get('is_norm_adj', True)
        self.num_class = cfg.get('num_class', 1)
        self.th_pos = cfg.get('th_pos', None)
        self.th_neg = cfg.get('th_neg', None)
        self.wo_weight = cfg.get('wo_weight', False)
        self.use_mask = cfg.get('use_mask', False)
        self.is_test = is_test

        self._read(feat_path, label_path, proposal_folders)

        print('#cluster: {}, #num_class: {}, feature shape: {}, '
              'norm_adj: {}, wo_weight: {}'.format(self.size, self.num_class,
                                                   self.features.shape,
                                                   self.is_norm_adj,
                                                   self.wo_weight))

    def _read(self, feat_path, label_path, proposal_folders):
        fn_node_pattern = '*_node.npz'
        fn_edge_pattern = '*_edge.npz'

        with Timer('read meta and feature'):
            if label_path is not None:
                self.lb2idxs, self.idx2lb = read_meta(label_path)
                self.labels = intdict2ndarray(self.idx2lb)
                self.inst_num = len(self.idx2lb)
                self.ignore_label = False
            else:
                self.lb2idxs, self.idx2lb = None, None
                self.labels = None
                self.inst_num = -1
                self.ignore_label = True
            if not self.featureless:
                features = read_probs(feat_path, self.inst_num,
                                      self.feature_dim)
                self.features = l2norm(features)
                if self.inst_num == -1:
                    self.inst_num = features.shape[0]
            else:
                assert self.inst_num > 0
                self.feature_dim = 1
                self.features = np.ones(self.inst_num).reshape(-1, 1)

        with Timer('read proposal list'):
            self.lst = []
            if callable(proposal_folders):
                proposal_folders = proposal_folders()
            for proposal_folder in proposal_folders:
                print('read proposals from folder: ', proposal_folder)
                fn_nodes = sorted(
                    glob.glob(os.path.join(proposal_folder, fn_node_pattern)))
                fn_edges = sorted(
                    glob.glob(os.path.join(proposal_folder, fn_edge_pattern)))
                assert len(fn_nodes) == len(
                    fn_edges), "node files({}) vs edge files({})".format(
                        len(fn_nodes), len(fn_edges))
                assert len(fn_nodes) > 0, 'files under {} is 0'.format(
                    proposal_folder)
                for fn_node, fn_edge in zip(fn_nodes, fn_edges):
                    assert fn_node[:fn_node.rfind(
                        '_')] == fn_edge[:fn_edge.rfind('_'
                                                        )], "{} vs {}".format(
                                                            fn_node, fn_edge)
                    self.lst.append([fn_node, fn_edge])
            self.size = len(self.lst)

    def __len__(self):
        return self.size
