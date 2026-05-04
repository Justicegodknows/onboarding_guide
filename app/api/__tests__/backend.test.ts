import { healthCheck, sendChat, API_URL } from '../backend';

describe('backend API helpers', () => {
    beforeEach(() => {
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

    describe('API_URL', () => {
        it('defaults to http://localhost:8000 when env var is not set', () => {
            expect(API_URL).toBe('http://localhost:8000');
        });
    });

    describe('healthCheck()', () => {
        it('calls /health and returns the response json', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ status: 'ok' }),
            });

            const result = await healthCheck();

            expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/health`);
            expect(result).toEqual({ status: 'ok' });
        });

        it('throws when the response is not ok', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });

            await expect(healthCheck()).rejects.toThrow('Health check failed');
        });
    });

    describe('sendChat()', () => {
        it('posts question and history, returns json', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ answer: 'Hello!' }),
            });

            const result = await sendChat('What is onboarding?', ['prev question']);

            expect(global.fetch).toHaveBeenCalledWith(
                `${API_URL}/api/v1/chat/`,
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: 'What is onboarding?',
                        history: ['prev question'],
                    }),
                })
            );
            expect(result).toEqual({ answer: 'Hello!' });
        });

        it('defaults history to an empty array', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ answer: 'Hi' }),
            });

            await sendChat('Question?');

            const body = JSON.parse(
                (global.fetch as jest.Mock).mock.calls[0][1].body
            );
            expect(body.history).toEqual([]);
        });

        it('throws when the response is not ok', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });

            await expect(sendChat('fail')).rejects.toThrow('Chat failed');
        });
    });
});
