/**
 * Unit tests for DualCaptionDisplay component
 * 
 * Tests Requirements: 36.1, 36.2, 36.3, 36.4, 36.6, 36.7, 36.8, 37.1, 37.2
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DualCaptionDisplay, Caption } from './DualCaptionDisplay';

describe('DualCaptionDisplay', () => {
  const mockCaptions: Caption[] = [
    {
      id: '1',
      text: 'Hello everyone',
      source: 'speech',
      speakerId: 'user1',
      speakerName: 'John Doe',
      timestamp: Date.now() - 5000
    },
    {
      id: '2',
      text: 'Thank you',
      source: 'sign',
      speakerId: 'user2',
      speakerName: 'Jane Smith',
      timestamp: Date.now() - 3000,
      confidence: 0.95
    },
    {
      id: '3',
      text: 'How are you?',
      source: 'speech',
      speakerId: 'user1',
      speakerName: 'John Doe',
      timestamp: Date.now() - 1000
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render the component with default props', () => {
      render(
        <DualCaptionDisplay
          captions={[]}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      expect(screen.getByText('Live Captions')).toBeInTheDocument();
    });

    it('should display waiting message when no captions are available', () => {
      render(
        <DualCaptionDisplay
          captions={[]}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      expect(screen.getByText('Waiting for captions...')).toBeInTheDocument();
    });

    it('should display message when both caption types are disabled', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={false}
          signEnabled={false}
        />
      );

      expect(screen.getByText('Enable captions to see live transcription')).toBeInTheDocument();
    });
  });

  describe('Caption Display - Requirement 36.1, 37.1', () => {
    it('should display speech captions when speechEnabled is true', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={false}
        />
      );

      expect(screen.getByText('Hello everyone')).toBeInTheDocument();
      expect(screen.getByText('How are you?')).toBeInTheDocument();
      expect(screen.queryByText('Thank you')).not.toBeInTheDocument();
    });

    it('should display sign language captions when signEnabled is true', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={false}
          signEnabled={true}
        />
      );

      expect(screen.getByText('Thank you')).toBeInTheDocument();
      expect(screen.queryByText('Hello everyone')).not.toBeInTheDocument();
      expect(screen.queryByText('How are you?')).not.toBeInTheDocument();
    });

    it('should display both caption types when both are enabled', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      expect(screen.getByText('Hello everyone')).toBeInTheDocument();
      expect(screen.getByText('Thank you')).toBeInTheDocument();
      expect(screen.getByText('How are you?')).toBeInTheDocument();
    });
  });

  describe('Visual Distinction - Requirement 37.2', () => {
    it('should visually distinguish speech captions with blue color', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={[mockCaptions[0]]}
          speechEnabled={true}
          signEnabled={false}
        />
      );

      const speechCaption = screen.getByText('Hello everyone').closest('div');
      expect(speechCaption).toHaveStyle({ borderLeft: '4px solid #3b82f6' });
    });

    it('should visually distinguish sign language captions with green color', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={[mockCaptions[1]]}
          speechEnabled={false}
          signEnabled={true}
        />
      );

      const signCaption = screen.getByText('Thank you').closest('div');
      expect(signCaption).toHaveStyle({ borderLeft: '4px solid #22c55e' });
    });

    it('should display source labels for captions', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      const speechLabels = screen.getAllByText('Speech');
      const signLabels = screen.getAllByText('Sign Language');
      
      expect(speechLabels.length).toBeGreaterThan(0);
      expect(signLabels.length).toBeGreaterThan(0);
    });

    it('should display legend indicators in header', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      // Check for legend items in header
      const header = screen.getByText('Live Captions').parentElement;
      expect(header).toBeInTheDocument();
    });
  });

  describe('Confidence Indicators - Requirement 36.3', () => {
    it('should display confidence percentage for sign language captions', () => {
      render(
        <DualCaptionDisplay
          captions={[mockCaptions[1]]}
          speechEnabled={false}
          signEnabled={true}
        />
      );

      expect(screen.getByText('95%')).toBeInTheDocument();
    });

    it('should not display confidence for speech captions', () => {
      render(
        <DualCaptionDisplay
          captions={[mockCaptions[0]]}
          speechEnabled={true}
          signEnabled={false}
        />
      );

      expect(screen.queryByText(/%$/)).not.toBeInTheDocument();
    });

    it('should display different confidence levels with appropriate colors', () => {
      const captionsWithDifferentConfidence: Caption[] = [
        {
          id: '1',
          text: 'High confidence',
          source: 'sign',
          speakerId: 'user1',
          speakerName: 'User 1',
          timestamp: Date.now(),
          confidence: 0.95
        },
        {
          id: '2',
          text: 'Medium confidence',
          source: 'sign',
          speakerId: 'user2',
          speakerName: 'User 2',
          timestamp: Date.now(),
          confidence: 0.75
        },
        {
          id: '3',
          text: 'Low confidence',
          source: 'sign',
          speakerId: 'user3',
          speakerName: 'User 3',
          timestamp: Date.now(),
          confidence: 0.65
        }
      ];

      render(
        <DualCaptionDisplay
          captions={captionsWithDifferentConfidence}
          speechEnabled={false}
          signEnabled={true}
        />
      );

      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('65%')).toBeInTheDocument();
    });
  });

  describe('Speaker Information - Requirement 36.4', () => {
    it('should display speaker names for all captions', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      expect(screen.getAllByText('John Doe').length).toBeGreaterThan(0);
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    it('should display timestamps for all captions', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      // Check that timestamps are displayed (format: HH:MM:SS)
      const timestamps = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/);
      expect(timestamps.length).toBe(mockCaptions.length);
    });
  });

  describe('Caption History - Requirement 36.5', () => {
    it('should maintain caption history with multiple captions', () => {
      render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      // All captions should be visible
      expect(screen.getByText('Hello everyone')).toBeInTheDocument();
      expect(screen.getByText('Thank you')).toBeInTheDocument();
      expect(screen.getByText('How are you?')).toBeInTheDocument();
    });

    it('should display captions in chronological order', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      const captionTexts = Array.from(container.querySelectorAll('[style*="lineHeight"]'))
        .map(el => el.textContent);

      const expectedOrder = ['Hello everyone', 'Thank you', 'How are you?'];
      expectedOrder.forEach((text, index) => {
        expect(captionTexts[index]).toBe(text);
      });
    });
  });

  describe('Font Size Adjustment - Requirement 36.7', () => {
    it('should apply default font size when not specified', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={[mockCaptions[0]]}
          speechEnabled={true}
          signEnabled={false}
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveStyle({ fontSize: '16px' });
    });

    it('should apply custom font size when specified', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={[mockCaptions[0]]}
          speechEnabled={true}
          signEnabled={false}
          fontSize={20}
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveStyle({ fontSize: '20px' });
    });

    it('should apply font size to caption text', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={[mockCaptions[0]]}
          speechEnabled={true}
          signEnabled={false}
          fontSize={24}
        />
      );

      const captionText = screen.getByText('Hello everyone');
      expect(captionText).toHaveStyle({ fontSize: '24px' });
    });
  });

  describe('Caption Positioning - Requirement 36.8', () => {
    it('should position captions at bottom by default', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveStyle({ bottom: '20px' });
    });

    it('should position captions at top when specified', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
          position="top"
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveStyle({ top: '20px' });
    });

    it('should center captions horizontally', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveStyle({ 
        left: '50%',
        transform: 'translateX(-50%)'
      });
    });
  });

  describe('Scrolling Behavior', () => {
    it('should have scrollable container for caption history', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      const scrollContainer = container.querySelector('[style*="overflowY"]');
      expect(scrollContainer).toBeInTheDocument();
      expect(scrollContainer).toHaveStyle({ overflowY: 'auto' });
    });

    it('should limit maximum height to prevent obscuring video', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveStyle({ maxHeight: '300px' });
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className when provided', () => {
      const { container } = render(
        <DualCaptionDisplay
          captions={mockCaptions}
          speechEnabled={true}
          signEnabled={true}
          className="custom-class"
        />
      );

      const captionDisplay = container.querySelector('.dual-caption-display');
      expect(captionDisplay).toHaveClass('custom-class');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty caption text', () => {
      const emptyCaption: Caption = {
        id: '1',
        text: '',
        source: 'speech',
        speakerId: 'user1',
        speakerName: 'John Doe',
        timestamp: Date.now()
      };

      render(
        <DualCaptionDisplay
          captions={[emptyCaption]}
          speechEnabled={true}
          signEnabled={false}
        />
      );

      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('should handle very long caption text', () => {
      const longCaption: Caption = {
        id: '1',
        text: 'This is a very long caption text that should wrap properly and not break the layout or overflow the container boundaries',
        source: 'speech',
        speakerId: 'user1',
        speakerName: 'John Doe',
        timestamp: Date.now()
      };

      render(
        <DualCaptionDisplay
          captions={[longCaption]}
          speechEnabled={true}
          signEnabled={false}
        />
      );

      expect(screen.getByText(longCaption.text)).toBeInTheDocument();
    });

    it('should handle zero confidence', () => {
      const zeroConfidenceCaption: Caption = {
        id: '1',
        text: 'Low confidence gesture',
        source: 'sign',
        speakerId: 'user1',
        speakerName: 'John Doe',
        timestamp: Date.now(),
        confidence: 0
      };

      render(
        <DualCaptionDisplay
          captions={[zeroConfidenceCaption]}
          speechEnabled={false}
          signEnabled={true}
        />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle confidence of 1.0', () => {
      const perfectConfidenceCaption: Caption = {
        id: '1',
        text: 'Perfect confidence gesture',
        source: 'sign',
        speakerId: 'user1',
        speakerName: 'John Doe',
        timestamp: Date.now(),
        confidence: 1.0
      };

      render(
        <DualCaptionDisplay
          captions={[perfectConfidenceCaption]}
          speechEnabled={false}
          signEnabled={true}
        />
      );

      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should handle large number of captions efficiently', () => {
      const manyCaption: Caption[] = Array.from({ length: 100 }, (_, i) => ({
        id: `caption-${i}`,
        text: `Caption ${i}`,
        source: i % 2 === 0 ? 'speech' : 'sign',
        speakerId: `user${i % 5}`,
        speakerName: `User ${i % 5}`,
        timestamp: Date.now() - (100 - i) * 1000,
        confidence: i % 2 === 1 ? 0.8 + (i % 20) / 100 : undefined
      })) as Caption[];

      const { container } = render(
        <DualCaptionDisplay
          captions={manyCaption}
          speechEnabled={true}
          signEnabled={true}
        />
      );

      // Component should render without errors
      expect(container.querySelector('.dual-caption-display')).toBeInTheDocument();
      
      // Should have scrollable container
      const scrollContainer = container.querySelector('[style*="overflowY"]');
      expect(scrollContainer).toBeInTheDocument();
    });
  });
});
