import { useState, useEffect } from 'react';
import { Dayjs } from 'dayjs';
import { TabType, BreadTiming } from '../types/bread.ts';
import { breadTimingApi } from '../services/api.ts';

export const useSavedMakes = (
  activeTab: TabType, 
  selectedDate: Dayjs | null,
  selectedDough: BreadTiming | null,
  setSelectedDough: (timing: BreadTiming | null) => void,
  populateFormWithTiming: (timing: BreadTiming) => void
) => {
  const [savedTimings, setSavedTimings] = useState<BreadTiming[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchSavedTimings = async (date: string) => {
      setIsLoading(true);
      try {
        const response = await breadTimingApi.list(1, 50, date); // Get by date filter
        setSavedTimings(response.timings);
      } catch (error) {
        console.error('Error fetching saved timings:', error);
        setSavedTimings([]);
      } finally {
        setIsLoading(false);
      }
    };

    // Only fetch when saved tab is active and date is selected
    if (activeTab === 'saved' && selectedDate) {
      const formattedDate = selectedDate.format('YYYY-MM-DD');
      fetchSavedTimings(formattedDate);
    }
  }, [activeTab, selectedDate]);

  const handleViewTiming = (timing: BreadTiming) => {
    populateFormWithTiming(timing);
    setSelectedDough(timing);
  };

  const refreshSavedTimings = () => {
    if (activeTab === 'saved' && selectedDate) {
      const formattedDate = selectedDate.format('YYYY-MM-DD');
      const fetchSavedTimings = async (date: string) => {
        setIsLoading(true);
        try {
          const response = await breadTimingApi.list(1, 50, date);
          setSavedTimings(response.timings);
        } catch (error) {
          console.error('Error fetching saved timings:', error);
          setSavedTimings([]);
        } finally {
          setIsLoading(false);
        }
      };
      fetchSavedTimings(formattedDate);
    }
  };

  return {
    savedMakes: savedTimings, // Keep same name for backward compatibility
    isLoading,
    handleViewMake: handleViewTiming, // Keep same name for backward compatibility
    refreshSavedMakes: refreshSavedTimings, // Keep same name for backward compatibility
    selectedDough,
    setSelectedDough,
  };
};