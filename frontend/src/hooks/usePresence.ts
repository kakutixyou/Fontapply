import { useState, useCallback } from 'react';

export interface UserCursor {
  user_id: string;
  session_id: string;
  cursor_position: { x: number; y: number };
  selected_glyph: string | null;
  color: string;  // カーソル色（ユーザーごと）
}

const USER_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', 
  '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
];

export const usePresence = () => {
  const [userCursors, setUserCursors] = useState<Map<string, UserCursor>>(new Map());

  const updateUserCursor = useCallback((
    userId: string,
    sessionId: string,
    x: number,
    y: number,
    selectedGlyph: string | null
  ) => {
    setUserCursors(prev => {
      const updated = new Map(prev);
      const colorIndex = (Array.from(updated.keys()).length) % USER_COLORS.length;
      
      updated.set(sessionId, {
        user_id: userId,
        session_id: sessionId,
        cursor_position: { x, y },
        selected_glyph: selectedGlyph,
        color: USER_COLORS[colorIndex]
      });
      
      return updated;
    });
  }, []);

  const removeUserCursor = useCallback((sessionId: string) => {
    setUserCursors(prev => {
      const updated = new Map(prev);
      updated.delete(sessionId);
      return updated;
    });
  }, []);

  return {
    userCursors: Array.from(userCursors.values()),
    updateUserCursor,
    removeUserCursor
  };
};
