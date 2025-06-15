import { useState, useEffect } from 'react';
import { Dayjs } from 'dayjs';
import { DoughMake, TabType } from '../types/bread.ts';
import { doughMakesApi } from '../services/api.ts';

export const useSavedMakes = (
  activeTab: TabType, 
  selectedDate: Dayjs | null,
  selectedDough: DoughMake | null,
  setSelectedDough: (dough: DoughMake | null) => void,
  populateFormWithDough: (dough: DoughMake) => void
) => {
  const [savedMakes, setSavedMakes] = useState<DoughMake[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchSavedMakes = async (date: string) => {
      setIsLoading(true);
      try {
        const makes = await doughMakesApi.getByDate(date);
        setSavedMakes(makes);
      } catch (error) {
        console.error('Error fetching saved makes:', error);
        setSavedMakes([]);
      } finally {
        setIsLoading(false);
      }
    };

    // Only fetch when saved tab is active and date is selected
    if (activeTab === 'saved' && selectedDate) {
      const formattedDate = selectedDate.format('YYYY-MM-DD');
      fetchSavedMakes(formattedDate);
    }
  }, [activeTab, selectedDate]);

  const handleViewMake = (make: DoughMake) => {
    populateFormWithDough(make);
    setSelectedDough(make);
  };

  const refreshSavedMakes = () => {
    if (activeTab === 'saved' && selectedDate) {
      const formattedDate = selectedDate.format('YYYY-MM-DD');
      const fetchSavedMakes = async (date: string) => {
        setIsLoading(true);
        try {
          const makes = await doughMakesApi.getByDate(date);
          setSavedMakes(makes);
        } catch (error) {
          console.error('Error fetching saved makes:', error);
          setSavedMakes([]);
        } finally {
          setIsLoading(false);
        }
      };
      fetchSavedMakes(formattedDate);
    }
  };

  return {
    savedMakes,
    isLoading,
    handleViewMake,
    refreshSavedMakes,
    selectedDough,
    setSelectedDough,
  };
};