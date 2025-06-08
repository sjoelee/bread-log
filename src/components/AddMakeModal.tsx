import React from 'react';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';

interface AddMakeModalProps {
  isOpen: boolean;
  newMakeName: string;
  onNameChange: (name: string) => void;
  onClose: () => void;
  onAdd: () => void;
  isAdding: boolean;
  error: string | null;
}

const modalStyle = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
};

export const AddMakeModal: React.FC<AddMakeModalProps> = ({
  isOpen,
  newMakeName,
  onNameChange,
  onClose,
  onAdd,
  isAdding,
  error,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd();
  };

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      aria-labelledby="add-make-modal-title"
      aria-describedby="add-make-modal-description"
    >
      <Box sx={modalStyle}>
        <h2 id="add-make-modal-title" className="text-lg font-medium mb-4">
          Add New Make
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <TextField
            fullWidth
            label="Make Name"
            value={newMakeName}
            onChange={(e) => onNameChange(e.target.value)}
            error={!!error}
            helperText={error}
            disabled={isAdding}
            autoFocus
          />
          
          <div className="flex gap-2 justify-end">
            <Button
              variant="outlined"
              onClick={onClose}
              disabled={isAdding}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              type="submit"
              disabled={isAdding || !newMakeName.trim()}
            >
              {isAdding ? 'Adding...' : 'Add Make'}
            </Button>
          </div>
        </form>
      </Box>
    </Modal>
  );
};