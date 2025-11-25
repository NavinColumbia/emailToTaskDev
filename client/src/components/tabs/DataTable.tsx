import { useState, type ReactNode } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Checkbox, Button, CircularProgress } from '@mui/material';
import { OpenInNew as OpenInNewIcon, Delete as DeleteIcon } from '@mui/icons-material';
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
  getItemLink?: (item: T) => string | undefined;
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
  getItemLink,
}: DataTableProps<T>) {
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

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
    const selectedData = data.filter(item => selectedItems.has(getItemId(item)) && getItemLink(item));
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (data.length === 0) {
    return (
      <Box 
        sx={{ 
          border: `1.5px solid ${notionColors.border.default}`, 
          borderRadius: '12px', 
          p: 6, 
          textAlign: 'center',
          backgroundColor: '#FFFFFF',
        }}
      >
        {emptyIcon}
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
          borderRadius: '12px',
          border: `1.5px solid ${notionColors.border.default}`,
          boxShadow: notionColors.shadow.card,
          backgroundColor: '#FFFFFF',
          '&::-webkit-scrollbar': {
            width: '6px',
            height: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#f1f1f1',
            borderRadius: '3px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: notionColors.primary.main,
            borderRadius: '3px',
            '&:hover': {
              background: notionColors.primary.dark,
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
                    color: notionColors.primary.main,
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
                    borderRight: `1.5px solid ${notionColors.border.default}`,
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
      {hasSelection && (onOpen || onDelete) && (
        <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center', justifyContent: 'flex-end' }}>
          {onOpen && getItemLink && (
            <Button
              variant="contained"
              startIcon={<OpenInNewIcon />}
              onClick={handleOpen}
              disabled={isDeleting}
              sx={{
                fontSize: '14px',
                px: 3,
                py: 1.25,
                borderRadius: '8px',
              }}
            >
              Open ({selectedItems.size})
            </Button>
          )}
          {onDelete && (
            <Button
              variant="contained"
              startIcon={<DeleteIcon />}
              onClick={handleDelete}
              disabled={isDeleting}
              sx={{
                fontSize: '14px',
                px: 3,
                py: 1.25,
                borderRadius: '8px',
              }}
            >
              {isDeleting ? 'Deleting...' : `Delete (${selectedItems.size})`}
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
}

