import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ChatBox from '../ChatBox';
import * as backend from '../../api/backend';

jest.mock('../../api/backend');

const mockSendChat = backend.sendChat as jest.MockedFunction<typeof backend.sendChat>;

describe('ChatBox component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders the heading, input and send button', () => {
        render(<ChatBox />);
        expect(screen.getByText('Chat with RAG Agent')).toBeInTheDocument();
        expect(screen.getByRole('textbox')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    it('disables the Send button when the input is empty', () => {
        render(<ChatBox />);
        expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
    });

    it('enables the Send button when the user types', async () => {
        render(<ChatBox />);
        await userEvent.type(screen.getByRole('textbox'), 'Hello');
        expect(screen.getByRole('button', { name: /send/i })).toBeEnabled();
    });

    it('shows the answer after a successful chat call', async () => {
        mockSendChat.mockResolvedValueOnce({ answer: 'Welcome aboard!' });

        render(<ChatBox />);
        await userEvent.type(screen.getByRole('textbox'), 'What is the onboarding process?');
        fireEvent.click(screen.getByRole('button', { name: /send/i }));

        await waitFor(() =>
            expect(screen.getByText(/Welcome aboard!/i)).toBeInTheDocument()
        );
    });

    it('clears the input after a successful submission', async () => {
        mockSendChat.mockResolvedValueOnce({ answer: 'Done' });

        render(<ChatBox />);
        const input = screen.getByRole('textbox');
        await userEvent.type(input, 'Some question');
        fireEvent.click(screen.getByRole('button', { name: /send/i }));

        await waitFor(() => expect(input).toHaveValue(''));
    });

    it('shows an error message when sendChat rejects', async () => {
        mockSendChat.mockRejectedValueOnce(new Error('Chat failed'));

        render(<ChatBox />);
        await userEvent.type(screen.getByRole('textbox'), 'Bad request');
        fireEvent.click(screen.getByRole('button', { name: /send/i }));

        await waitFor(() =>
            expect(screen.getByText(/Chat failed/i)).toBeInTheDocument()
        );
    });

    it('prepends the department to the question when department prop is provided', async () => {
        mockSendChat.mockResolvedValueOnce({ answer: 'HR answer' });

        render(<ChatBox department="HR" />);
        await userEvent.type(screen.getByRole('textbox'), 'Benefits?');
        fireEvent.click(screen.getByRole('button', { name: /send/i }));

        await waitFor(() => expect(mockSendChat).toHaveBeenCalledWith(
            '[HR] Benefits?',
            expect.any(Array)
        ));
    });

    it('shows a department-specific placeholder', () => {
        render(<ChatBox department="Engineering" />);
        expect(
            screen.getByPlaceholderText('Ask about Engineering...')
        ).toBeInTheDocument();
    });
});
