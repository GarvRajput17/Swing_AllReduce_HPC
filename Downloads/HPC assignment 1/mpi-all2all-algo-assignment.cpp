//IMT2023505 Garv Rajput

#include <iostream>
#include <vector>
#include <numeric>
#include <cstdlib>
#include <functional>
#include <cassert>
#include "mpi.h"
using namespace std;

void print_buffer(const string& label, int rank, const vector<int>& buffer) {
    cout << "Rank " << rank << " " << label << ": ";
    for (size_t i = 0; i < buffer.size(); ++i) {
        cout << buffer[i] << " ";
    }
    cout << endl;
}

// Helper class to manage the Fat-Tree Topology and Rank/Tuple Conversions
class FatTreeTopology {
private:
    vector<int> M; // Dimensions of the fat-tree, e.g., {M1, M2, ...}
    int L;              // Number of levels in the fat-tree
    int N;              // Total number of processes

public:
    FatTreeTopology(const vector<int>& m_values) : M(m_values) {
        L = M.size();
        N = 1;
        for (int val : M) {
            N *= val;
        }
    }

    int get_num_procs() const { 
        return N; 
    }
    int get_num_levels() const { 
        return L; 
    }

    // Converts an integer rank to a tuple representation, e.g., rank 5 -> (1, 1) for M={4,2}
    vector<int> rank_to_tuple(int rank) const {
        vector<int> tuple(L);
        int temp_rank = rank;
        for (int i = 0; i < L; ++i) {
            tuple[i] = temp_rank % M[i];
            temp_rank /= M[i];
        }
        return tuple;
    }

    // Converts a tuple representation back to an integer rank
    int tuple_to_rank(const vector<int>& tuple) const {
        int rank = 0;
        int multiplier = 1;
        for (int i = 0; i < L; ++i) {
            rank += tuple[i] * multiplier;
            multiplier *= M[i];
        }
        return rank;
    }

    // Implements the core formula from the paper to find the communication partner
    int get_dest_rank(int my_rank, int phase) const {
        vector<int> s = rank_to_tuple(my_rank);
        vector<int> k = rank_to_tuple(phase);
        vector<int> d(L);

        for (int i = 0; i < L; ++i) {
            // This is Equation (2) from the paper
            d[i] = (s[i] + k[i]) % M[i];
        }

        return tuple_to_rank(d);
    }

    int get_source_rank(int my_rank, int phase) const {
        vector<int> d = rank_to_tuple(my_rank);
        vector<int> k = rank_to_tuple(phase);
        vector<int> s(L);

        for (int i = 0; i < L; ++i) {
            s[i] = (d[i] - k[i] + M[i]) % M[i];
        }

        return tuple_to_rank(s);
    }
};


// The main function for the topology-aware All-to-All

void FatTreeAlltoall(const int* send_buf, int chunk_size, int* recv_buf, const FatTreeTopology& topo, MPI_Comm comm) {
    int rank, size;
    MPI_Comm_rank(comm, &rank);
    MPI_Comm_size(comm, &size);
    
    assert(size == topo.get_num_procs());

    for (int phase = 0; phase < size; ++phase) {
        int dest_rank = topo.get_dest_rank(rank, phase);
        int source_rank = topo.get_source_rank(rank, phase);

        const int* chunk_to_send_ptr = &send_buf[dest_rank * chunk_size];
        int* chunk_to_recv_ptr = &recv_buf[source_rank * chunk_size];

        if (dest_rank == rank) {
            // A self-send is just a local copy. The source must also be self.
            for (int i = 0; i < chunk_size; ++i) {
                chunk_to_recv_ptr[i] = chunk_to_send_ptr[i];
            }
        } else {
            MPI_Sendrecv(chunk_to_send_ptr, chunk_size, MPI_INT, dest_rank, 0,
                         chunk_to_recv_ptr, chunk_size, MPI_INT, source_rank, 0,
                         comm, MPI_STATUS_IGNORE);
        }
    }
}

// Helper function to find prime factors of an integer.
vector<int> get_factors(int n) {
    vector<int> factors;
    if (n <= 0) return factors;
    if (n == 1) {
        factors.push_back(1);
        return factors;
    }
    int d = 2;
    while (d * d <= n) {
        while (n % d == 0) {
            factors.push_back(d);
            n /= d;
        }
        d++;
    }
    if (n > 1) {
        factors.push_back(n);
    }
    return factors;
}

// Helper function to check if a number is a power of two.
bool is_power_of_two(int n) {
    return (n > 0) && ((n & (n - 1)) == 0);
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int local_success;
    int global_success;

    // --- 1. Data Initialization ---
    vector<int> sendbuf(size);
    vector<int> recvbuf(size);

    // Fill send buffer with distinct values.
    for (int i = 0; i < size; ++i) {
        sendbuf[i] = rank * 100 + i; // Example: rank 2 sends {200, 201, 202, ...}
    }

    if (rank == 0) {
        cout << "\n--- Initial Sent Data ---" << endl;
    }
    MPI_Barrier(MPI_COMM_WORLD);
    for (int i = 0; i < size; ++i) {
        if (rank == i) {
            print_buffer("sent", rank, sendbuf);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }

    // --- Baseline: Using MPI_Alltoall ---
    if (rank == 0) {
        //cout << "\n--- Baseline: MPI_Alltoall ---" << endl;
    }
    MPI_Barrier(MPI_COMM_WORLD);
    MPI_Alltoall(sendbuf.data(), 1, MPI_INT, recvbuf.data(), 1, MPI_INT, MPI_COMM_WORLD);
    for (int i = 0; i < size; ++i) {
        if (rank == i) {
            print_buffer("received (MPI_Alltoall)", rank, recvbuf);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }

    // --- Task 1: Pairwise Exchange Algorithm Implementation ---
    if (rank == 0) {
        cout << "\n--- Algorithm 1: Pairwise Exchange ---" << endl;
    }
    MPI_Barrier(MPI_COMM_WORLD);
    
    vector<int> pairwise_recvbuf(size);

    if (is_power_of_two(size)) {
        // Step 0: self-communication (rank -> rank)
        pairwise_recvbuf[rank] = sendbuf[rank];

        // Steps 1 to size-1: exchange with partners
        for (int i = 1; i < size; ++i) {
            int partner = rank ^ i;
            MPI_Sendrecv(&sendbuf[partner], 1, MPI_INT, partner, 0,
                         &pairwise_recvbuf[partner], 1, MPI_INT, partner, 0,
                         MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        for (int i = 0; i < size; ++i) {
            if (rank == i) {
                print_buffer("received (Pairwise)", rank, pairwise_recvbuf);
            }
            MPI_Barrier(MPI_COMM_WORLD);
        }
        
        // Verification
        local_success = 1; // Use int for MPI_Reduce
        for (int i = 0; i < size; ++i) {
            if (recvbuf[i] != pairwise_recvbuf[i]) {
                cerr << "Rank " << rank << " FAILED pairwise verification at index " << i
                          << ". Expected " << recvbuf[i] << ", got " << pairwise_recvbuf[i] << endl;
                local_success = 0;
            }
        }
        
        global_success = 0;
        MPI_Reduce(&local_success, &global_success, 1, MPI_INT, MPI_LAND, 0, MPI_COMM_WORLD);
        
        if (rank == 0) {
            if (global_success) {
                cout << "SUCCESS: Pairwise exchange implementation is correct." << endl;
            } else {
                cout << "FAILURE: Pairwise exchange implementation has errors." << endl;
            }
        }
    } else {
        if (rank == 0) {
            cout << "NOTE: Pairwise exchange algorithm requires a power-of-two number of processes, skipping." << endl;
        }
    }

    // --- Task 2: Linear Exchange Algorithm Implementation ---
    if (rank == 0) {
        cout << "\n--- Algorithm 2: Linear Exchange ---" << endl;
    }
    MPI_Barrier(MPI_COMM_WORLD);

    vector<int> linear_recvbuf(size);

    // Phase 0 (p=0): self-copy
    linear_recvbuf[rank] = sendbuf[rank];

    // Phases 1 to size-1
    for (int p = 1; p < size; ++p) {
        int dest_rank = (rank + p) % size;
        int source_rank = (rank - p + size) % size;
        MPI_Sendrecv(&sendbuf[dest_rank], 1, MPI_INT, dest_rank, 0,
                     &linear_recvbuf[source_rank], 1, MPI_INT, source_rank, 0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }

    for (int i = 0; i < size; ++i) {
        if (rank == i) {
            print_buffer("received (Linear)", rank, linear_recvbuf);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }
    
    // Verification for Linear Exchange
    local_success = 1;
    for (int i = 0; i < size; ++i) {
        if (recvbuf[i] != linear_recvbuf[i]) {
            cerr << "Rank " << rank << " FAILED linear verification at index " << i
                      << ". Expected " << recvbuf[i] << ", got " << linear_recvbuf[i] << endl;
            local_success = 0;
        }
    }
    
    global_success = 0;
    MPI_Reduce(&local_success, &global_success, 1, MPI_INT, MPI_LAND, 0, MPI_COMM_WORLD);
    
    if (rank == 0) {
        if (global_success) {
            cout << "SUCCESS: Linear exchange implementation is correct." << endl;
        } else {
            cout << "FAILURE: Linear exchange implementation has errors." << endl;
        }
    }

    // --- Task 3: Torsten's bandwidth optimal alltoall algorithm Algorithm ---
    if (rank == 0) {
        cout << "\n--- Algorithm 3: Torsten's bandwidth optimal alltoall algorithm Exchange ---" << endl;
    }
    MPI_Barrier(MPI_COMM_WORLD);

    vector<int> fattree_recvbuf(size);
    
    // Define the Fat-Tree Topology based on prime factorization of size
    vector<int> M = get_factors(size); 
    FatTreeTopology topo(M);

    // Run the All-to-All Algorithm
    FatTreeAlltoall(sendbuf.data(), 1, fattree_recvbuf.data(), topo, MPI_COMM_WORLD);

    for (int i = 0; i < size; ++i) {
        if (rank == i) {
            print_buffer("received (All-2-All)", rank, fattree_recvbuf);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }

    // Verification for Fat-Tree Exchange
    local_success = 1;
    for (int i = 0; i < size; ++i) {
        if (recvbuf[i] != fattree_recvbuf[i]) {
            cerr << "Rank " << rank << " FAILED Torsten's bandwidth optimal alltoall algorithm verification at index " << i
                        << ". Expected " << recvbuf[i] << ", got " << fattree_recvbuf[i] << endl;
            local_success = 0;
        }
    }
    
    global_success = 0;
    MPI_Reduce(&local_success, &global_success, 1, MPI_INT, MPI_LAND, 0, MPI_COMM_WORLD);
    
    if (rank == 0) {
        if (global_success) {
            cout << "SUCCESS: Torsten's bandwidth optimal alltoall algorithm  implementation is correct." << endl;
        } else {
            cout << "FAILURE: Torsten's bandwidth optimal alltoall algorithm implementation has errors." << endl;
        }
    }

    // clear the buffers
    sendbuf.clear();
    recvbuf.clear();
    pairwise_recvbuf.clear();
    linear_recvbuf.clear();
    fattree_recvbuf.clear();

    MPI_Finalize();
    return 0;
}
