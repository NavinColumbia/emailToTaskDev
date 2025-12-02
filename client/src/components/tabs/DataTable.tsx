import { useState, type ReactNode } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Checkbox, Button, CircularProgress } from '@mui/material';
import { OpenInNew as OpenInNewIcon, Delete as DeleteIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { notionColors } from '../../theme';

export interface Column<T> {
  header: string;
  width?: string;
  minWidth?: string;
  maxWidth?: string;
  render: (item: T) => ReactNode;
}

interface DataTableProps<T> {
  data: T[];
  loading: boolean;
  columns: Column<T>[];
  emptyIcon?: ReactNode;
  emptyTitle: string;
  emptyMessage: string;
  getItemId: (item: T) => number;
  onOpen?: (items: T[]) => void;
  onDelete?: (itemIds: number[]) => Promise<void>;
  onConfirm?: (itemIds: number[]) => Promise<void>;
  getItemLink?: (item: T) => string | undefined;
  getItemStatus?: (item: T) => string | undefined;
}

export default function DataTable<T>({
  data,
  loading,
  columns,
  emptyIcon,
  emptyTitle,
  emptyMessage,
  getItemId,
  onOpen,
  onDelete,
  onConfirm,
  getItemLink,
  getItemStatus,
}: DataTableProps<T>) {
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const handleSelectItem = (itemId: number) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedItems.size === data.length) {
      setSelectedItems(new Set());
    } else {
      const allIds = new Set(data.map(item => getItemId(item)));
      setSelectedItems(allIds);
    }
  };

  const allSelected = data.length > 0 && selectedItems.size === data.length;
  const someSelected = selectedItems.size > 0 && selectedItems.size < data.length;
  const hasSelection = selectedItems.size > 0;

  const handleOpen = () => {
    if (!onOpen || !getItemLink) return;
    const selectedData = data.filter(item => selectedItems.has(getItemId(item)) && getItemLink && getItemLink(item));
    if (selectedData.length > 0) {
      onOpen(selectedData);
    }
  };

  const handleDelete = async () => {
    if (!onDelete || !hasSelection) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedItems.size} item(s)? This action cannot be undone.`)) {
      return;
    }

    setIsDeleting(true);
    try {
      const selectedIds = Array.from(selectedItems);
      await onDelete(selectedIds);
      setSelectedItems(new Set());
    } catch (error) {
      console.error('Failed to delete items:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete items');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleConfirm = async () => {
    if (!onConfirm || !hasSelection) return;
    
    // Filter to only pending items
    const pendingIds = data
      .filter(item => selectedItems.has(getItemId(item)) && getItemStatus && getItemStatus(item) === 'pending')
      .map(item => getItemId(item));
    
    if (pendingIds.length === 0) {
      alert('No pending items selected. Please select items with "Pending" status.');
      return;
    }

    setIsConfirming(true);
    try {
      await onConfirm(pendingIds);
      setSelectedItems(new Set());
    } catch (error) {
      console.error('Failed to confirm items:', error);
      alert(error instanceof Error ? error.message : 'Failed to confirm items');
    } finally {
      setIsConfirming(false);
    }
  };

  // Check if any selected items are pending
  const hasPendingSelection = selectedItems.size > 0 && data.some(
    item => selectedItems.has(getItemId(item)) && getItemStatus && getItemStatus(item) === 'pending'
  );

  const hasOpenableSelection = selectedItems.size > 0 && getItemLink && data.some(
    item => selectedItems.has(getItemId(item)) && getItemLink(item)
  );

  if (data.length === 0) {
    return (
      <Box 
        sx={{ 
          border: `1.5px solid ${notionColors.border.light}`, 
          borderRadius: 0, 
          p: 6, 
          textAlign: 'center',
          backgroundColor: '#FFFFFF',
          boxShadow: notionColors.shadow.card,
        }}
      >
        {loading ? (
          <CircularProgress size={48} sx={{ mb: 2, color: 'lightgray' }} />
        ) : (
          emptyIcon
        )}
        <Typography variant="h6" sx={{ mb: 1, fontSize: '16px', fontWeight: 600, color: notionColors.text.primary }}>
          {emptyTitle}
        </Typography>
        <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
          {emptyMessage}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <TableContainer 
        sx={{ 
          width: '100%', 
          maxHeight: '50vh', 
          overflow: 'auto', 
          position: 'relative',
          borderRadius: 0,
          border: `1.5px solid ${notionColors.border.light}`,
          boxShadow: notionColors.shadow.card,
          backgroundColor: '#FFFFFF',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#F1F5F9',
            borderRadius: 0,
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'linear-gradient(135deg, #60A5FA 0%, #2563EB 100%)',
            borderRadius: 0,
            border: '2px solid #F1F5F9',
            '&:hover': {
              background: 'linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%)',
            },
          },
        }}
      >
        <Table sx={{ width: '100%', tableLayout: 'auto' }}>
          <TableHead>
            <TableRow>
              <TableCell 
                sx={{ 
                  width: '20px', 
                  minWidth: '20px',
                  position: 'sticky',
                  left: 0,
                  top: 0,
                  zIndex: 3,
                  backgroundColor: '#FFFFFF',
                  borderRight: `1.5px solid ${notionColors.border.default}`,
                }}
              >
                <Checkbox
                  checked={allSelected}
                  indeterminate={someSelected}
                  onChange={handleSelectAll}
                  size="small"
                />
              </TableCell>
              {columns.map((column, index) => (
                <TableCell
                  key={index}
                  sx={{
                    width: column.width || '150px',
                    minWidth: column.minWidth || '100px',
                    position: 'sticky',
                    top: 0,
                    zIndex: 2,
                    backgroundColor: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '13px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: notionColors.text.secondary,
                    borderBottom: `2px solid ${notionColors.border.light}`,
                  }}
                >
                  {column.header}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item) => (
              <TableRow key={getItemId(item)}>
                <TableCell 
                  sx={{ 
                    width: '20px', 
                    minWidth: '20px',
                    position: 'sticky',
                    left: 0,
                    zIndex: 1,
                    backgroundColor: '#FFFFFF',
                    borderRight: `1.5px solid ${notionColors.border.light}`,
                  }}
                >
                  <Checkbox
                    checked={selectedItems.has(getItemId(item))}
                    onChange={() => handleSelectItem(getItemId(item))}
                    size="small"
                  />
                </TableCell>
                {columns.map((column, index) => (
                  <TableCell
                    key={index}
                    sx={{
                      width: column.width || '150px',
                      minWidth: column.minWidth || '100px',
                      backgroundColor: '#FFFFFF',
                    }}
                  >
                    {column.render(item)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {hasSelection && (onOpen || onDelete || onConfirm) && (
        <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center', justifyContent: 'flex-end' }}>
          {onConfirm && hasPendingSelection && (
            <Button
              variant="outlined"
              startIcon={isConfirming ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              onClick={handleConfirm}
              disabled={isConfirming || isDeleting}
              sx={{
                px: 3,
                py: 1.25,
                borderColor: notionColors.warning?.main || '#F5A623',
                color: notionColors.warning?.main || '#F5A623',
                '&:hover': {
                  borderColor: notionColors.warning?.dark || '#D68910',
                  backgroundColor: notionColors.warning?.background || '#FFF4E5',
                },
              }}
            >
              {isConfirming ? 'Confirming...' : `Confirm (${data.filter(item => selectedItems.has(getItemId(item)) && getItemStatus && getItemStatus(item) === 'pending').length})`}
            </Button>
          )}
          {onOpen && getItemLink && hasOpenableSelection && (
            <Button
              variant="outlined"
              startIcon={<OpenInNewIcon />}
              onClick={handleOpen}
              disabled={isDeleting || isConfirming}
              sx={{
                px: 3,
                py: 1.25,
              }}
            >
              Open ({data.filter(item => selectedItems.has(getItemId(item)) && getItemLink && getItemLink(item)).length})
            </Button>
          )}
          {onDelete && (
            <Button
              variant="outlined"
              startIcon={isDeleting ? <CircularProgress size={20} /> : <DeleteIcon />}
              onClick={handleDelete}
              disabled={isDeleting || isConfirming}
              sx={{
                px: 3,
                py: 1.25,
                borderColor: notionColors.error.text,
                color: notionColors.error.text,
                '&:hover': {
                  borderColor: '#B91C1C',
                  backgroundColor: notionColors.error.background,
                },
              }}
            >
              {`Delete (${selectedItems.size})`}
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
}

