import { useState, useEffect } from 'react';
import { TeamMake, DEFAULT_TEAM_MAKES, CreateMakeRequest } from '../types/bread.ts';
import { teamMakesApi } from '../services/api.ts';

export const useTeamMakes = () => {
  const [teamMakes, setTeamMakes] = useState<TeamMake[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAddMakeModalOpen, setIsAddMakeModalOpen] = useState(false);
  const [newMakeName, setNewMakeName] = useState('');
  const [isAddingMake, setIsAddingMake] = useState(false);
  const [addMakeError, setAddMakeError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTeamMakes = async () => {
      setIsLoading(true);
      try {
        // Try to get cached data first
        const cached = localStorage.getItem('teamMakes');
        if (cached) {
          setTeamMakes(JSON.parse(cached));
        }

        // Fetch fresh data from API
        const data = await teamMakesApi.getAll();
        if (data.length > 0) {
          setTeamMakes(data);
          localStorage.setItem('teamMakes', JSON.stringify(data));
        } else {
          // Fall back to default makes if API returns empty
          setTeamMakes(DEFAULT_TEAM_MAKES);
        }
      } catch (error) {
        console.error('Error fetching team makes:', error);
        setTeamMakes(DEFAULT_TEAM_MAKES);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeamMakes();
  }, []);

  const openAddMakeModal = () => {
    setIsAddMakeModalOpen(true);
    setNewMakeName('');
    setAddMakeError(null);
  };

  const closeAddMakeModal = () => {
    setIsAddMakeModalOpen(false);
    setNewMakeName('');
    setAddMakeError(null);
  };

  const handleAddMake = async () => {
    if (!newMakeName.trim()) {
      setAddMakeError('Make name is required');
      return;
    }

    // Check if make already exists
    const makeKey = newMakeName.toLowerCase().replace(/\s+/g, '_');
    const exists = teamMakes.some(make => make.key === makeKey);
    if (exists) {
      setAddMakeError('A make with a similar name already exists');
      return;
    }

    setIsAddingMake(true);
    setAddMakeError(null);

    try {
      const displayName = newMakeName.trim();
      const key = displayName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
      
      const request: CreateMakeRequest = {
        display_name: displayName,
        key: key
      };

      const newMake = await teamMakesApi.create(request);
      
      // Update local state
      const updatedMakes = [...teamMakes, newMake];
      setTeamMakes(updatedMakes);
      localStorage.setItem('teamMakes', JSON.stringify(updatedMakes));
      
      closeAddMakeModal();
    } catch (error) {
      setAddMakeError(error instanceof Error ? error.message : 'Failed to add make');
    } finally {
      setIsAddingMake(false);
    }
  };

  return {
    teamMakes,
    setTeamMakes,
    isLoading,
    isAddMakeModalOpen,
    newMakeName,
    setNewMakeName,
    isAddingMake,
    addMakeError,
    openAddMakeModal,
    closeAddMakeModal,
    handleAddMake,
  };
};