import create from 'zustand';

interface CollaborationState {
  activeUsers: any[];
  remoteOperations: any[];
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
  
  setActiveUsers: (users: any[]) => void;
  addRemoteOperation: (op: any) => void;
  clearRemoteOperations: () => void;
  setConnectionStatus: (status: any) => void;
}

export const useCollaborationStore = create<CollaborationState>((set) => ({
  activeUsers: [],
  remoteOperations: [],
  connectionStatus: 'disconnected',

  setActiveUsers: (users) => set({ activeUsers: users }),
  addRemoteOperation: (op) =>
    set(state => ({
      remoteOperations: [...state.remoteOperations, op]
    })),
  clearRemoteOperations: () => set({ remoteOperations: [] }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
