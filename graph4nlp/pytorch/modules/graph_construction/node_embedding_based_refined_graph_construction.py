import torch
from torch import nn

from .base import DynamicGraphConstructionBase
from .utils import sparsify_graph, convert_adj_to_dgl_graph
from ..utils.constants import INF


class NodeEmbeddingBasedRefinedGraphConstruction(DynamicGraphConstructionBase):
    """Class for node embedding based refined dynamic graph construction.

    Parameters
    ----------
    word_vocab : Vocab
        The word vocabulary.
    embedding_styles : dict
        - ``word_emb_type`` : Specify pretrained word embedding types
            including "w2v" and/or "bert".
        - ``node_edge_emb_strategy`` : Specify node/edge embedding
            strategies including "mean", "lstm", "gru", "bilstm" and "bigru".
        - ``seq_info_encode_strategy`` : Specify strategies of encoding
            sequential information in raw text data including "none",
            "lstm", "gru", "bilstm" and "bigru".
    hidden_size : int, optional
        The hidden size of RNN layer, default: ``None``.
    fix_word_emb : boolean, optional
        Specify whether to fix pretrained word embeddings, default: ``True``.
    dropout : float, optional
        Dropout ratio, default: ``None``.
    device : torch.device, optional
        Specify computation device (e.g., CPU), default: ``None`` for using CPU.
    """

    def __init__(self, word_vocab, embedding_styles, input_size, hidden_size,
                        top_k, fix_word_emb=True, dropout=None, device=None):
        super(NodeEmbeddingBasedRefinedGraphConstruction, self).__init__(word_vocab,
                                                            embedding_styles,
                                                            hidden_size=hidden_size,
                                                            fix_word_emb=fix_word_emb,
                                                            dropout=dropout,
                                                            device=device)
        self.top_k = top_k
        self.device = device
        self.linear_sim = nn.Linear(input_size, hidden_size, bias=False)

    def forward(self, raw_text_data):
        """Compute graph topology and initial node/edge embeddings.

        Parameters
        ----------
        raw_text_data : list of sequences.
            The raw text data.
        **kwargs
            Extra parameters.

        Raises
        ------
        NotImplementedError
            NotImplementedError.
        """
        # nx_graph = text_data_to_static_graph(raw_text_data)

        # node_feat = get_node_feat(nx_graph)
        # node_emb = self.embedding(node_feat)

        # node_mask = get_node_mask(nx_graph)

        # dgl_graph = self.topology(node_emb, node_mask)
        # dgl_graph.ndata['x'] = node_emb

        # return dgl_graph
        pass

    def topology(self, node_emb, init_adj, alpha, node_mask=None):

        """Compute graph topology.

        Parameters
        ----------
        node_emb : torch.Tensor
            The node embeddings.
        init_adj : torch.sparse.FloatTensor
            The initial adjacency matrix, default: ``None``.
        node_mask : torch.Tensor, optional
            The node mask matrix, default: ``None``.

        """
        assert 0 <= alpha <= 1
        attention = self.self_attention(node_emb, node_mask)
        adj = sparsify_graph(attention, self.top_k, -INF, device=self.device)
        adj = torch.softmax(adj, dim=-1)

        new_adj = torch.sparse.FloatTensor.add((1 - alpha) * adj, alpha * init_adj)
        dgl_graph = convert_adj_to_dgl_graph(new_adj, 0, use_edge_softmax=False)

        return dgl_graph


    def embedding(self, feat, **kwargs):
        """Compute initial node/edge embeddings.

        Parameters
        ----------
        **kwargs
            Extra parameters.

        """
        # emb = self.embedding_layer(feat)
        # return emb
        pass

    def raw_text_to_init_graph(self, raw_text_data, **kwargs):
        """Convert raw text data to initial static graph.

        Parameters
        ----------
        raw_text_data : list of sequences.
            The raw text data.
        **kwargs
            Extra parameters.

        """
        pass

    def self_attention(self, node_emb, node_mask=None):
        """Computing an attention matrix for a fully connected graph
        """
        node_vec_t = torch.relu(self.linear_sim(node_emb))
        attention = torch.matmul(node_vec_t, node_vec_t.transpose(-1, -2))

        if node_mask is not None:
            attention = attention.masked_fill_(1 - node_mask.byte().unsqueeze(1), -INF)

        return attention
