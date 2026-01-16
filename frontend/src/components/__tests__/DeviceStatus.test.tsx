import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import DeviceStatus from '../device/DeviceStatus'
import type { DeviceStatus as DeviceStatusType } from '../../lib/api'
import type { ConnectionState } from '../../hooks/useDevice'

describe('DeviceStatus', () => {
  const mockConnectedStatus: DeviceStatusType = {
    connected: true,
    port: '/dev/cu.usbmodem4001',
    version: '1.4.0',
    hardware: 'TinySA Ultra',
    device_type: 'tinySA Ultra',
  }

  const mockDisconnectedStatus: DeviceStatusType = {
    connected: false,
    port: null,
    version: null,
    hardware: null,
    device_type: null,
  }

  describe('Connection States', () => {
    it('renders disconnected state correctly', () => {
      render(
        <DeviceStatus status={mockDisconnectedStatus} connectionState="disconnected" />
      )

      expect(screen.getByText('Device Status')).toBeInTheDocument()
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
      expect(
        screen.getByText('No device connected. Select a port and click Connect.')
      ).toBeInTheDocument()
    })

    it('renders connecting state correctly', () => {
      render(
        <DeviceStatus status={mockDisconnectedStatus} connectionState="connecting" />
      )

      expect(screen.getByText('Connecting')).toBeInTheDocument()
      expect(screen.getByText('Establishing connection...')).toBeInTheDocument()
    })

    it('renders connected state correctly', () => {
      render(
        <DeviceStatus status={mockConnectedStatus} connectionState="connected" />
      )

      expect(screen.getByText('Connected')).toBeInTheDocument()
      // Should not show the "No device connected" message
      expect(
        screen.queryByText('No device connected. Select a port and click Connect.')
      ).not.toBeInTheDocument()
    })

    it('renders disconnecting state correctly', () => {
      render(
        <DeviceStatus status={mockConnectedStatus} connectionState="disconnecting" />
      )

      expect(screen.getByText('Disconnecting')).toBeInTheDocument()
    })
  })

  describe('Device Information Display', () => {
    it('displays device type when connected', () => {
      render(
        <DeviceStatus status={mockConnectedStatus} connectionState="connected" />
      )

      expect(screen.getByText('Device')).toBeInTheDocument()
      expect(screen.getByText('tinySA Ultra')).toBeInTheDocument()
    })

    it('displays firmware version when connected', () => {
      render(
        <DeviceStatus status={mockConnectedStatus} connectionState="connected" />
      )

      expect(screen.getByText('Firmware')).toBeInTheDocument()
      expect(screen.getByText('1.4.0')).toBeInTheDocument()
    })

    it('displays hardware info when connected', () => {
      render(
        <DeviceStatus status={mockConnectedStatus} connectionState="connected" />
      )

      expect(screen.getByText('Hardware')).toBeInTheDocument()
      expect(screen.getByText('TinySA Ultra')).toBeInTheDocument()
    })

    it('displays port when connected', () => {
      render(
        <DeviceStatus status={mockConnectedStatus} connectionState="connected" />
      )

      expect(screen.getByText('Port')).toBeInTheDocument()
      expect(screen.getByText('/dev/cu.usbmodem4001')).toBeInTheDocument()
    })

    it('does not display device info when status is null', () => {
      render(<DeviceStatus status={null} connectionState="disconnected" />)

      expect(screen.queryByText('Device')).not.toBeInTheDocument()
      expect(screen.queryByText('Firmware')).not.toBeInTheDocument()
      expect(screen.queryByText('Hardware')).not.toBeInTheDocument()
      expect(screen.queryByText('Port')).not.toBeInTheDocument()
    })

    it('does not display device info when disconnected', () => {
      render(
        <DeviceStatus status={mockDisconnectedStatus} connectionState="disconnected" />
      )

      expect(screen.queryByText('Device')).not.toBeInTheDocument()
      expect(screen.queryByText('Firmware')).not.toBeInTheDocument()
    })
  })

  describe('Partial Device Information', () => {
    it('handles status with only some fields populated', () => {
      const partialStatus: DeviceStatusType = {
        connected: true,
        port: '/dev/ttyACM0',
        version: '1.3.0',
        hardware: null,
        device_type: null,
      }

      render(
        <DeviceStatus status={partialStatus} connectionState="connected" />
      )

      expect(screen.getByText('Firmware')).toBeInTheDocument()
      expect(screen.getByText('1.3.0')).toBeInTheDocument()
      expect(screen.getByText('Port')).toBeInTheDocument()
      expect(screen.getByText('/dev/ttyACM0')).toBeInTheDocument()
      // Should not display fields with null values
      expect(screen.queryByText('Device')).not.toBeInTheDocument()
      expect(screen.queryByText('Hardware')).not.toBeInTheDocument()
    })
  })

  describe('Status Indicator', () => {
    const connectionStates: ConnectionState[] = [
      'disconnected',
      'connecting',
      'connected',
      'disconnecting',
    ]

    connectionStates.forEach((state) => {
      it(`renders status indicator for ${state} state`, () => {
        render(
          <DeviceStatus status={mockDisconnectedStatus} connectionState={state} />
        )

        // Verify the state label is rendered
        const expectedLabels: Record<ConnectionState, string> = {
          disconnected: 'Disconnected',
          connecting: 'Connecting',
          connected: 'Connected',
          disconnecting: 'Disconnecting',
        }
        expect(screen.getByText(expectedLabels[state])).toBeInTheDocument()
      })
    })
  })
})
