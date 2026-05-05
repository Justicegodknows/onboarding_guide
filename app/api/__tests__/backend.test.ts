import {
    healthCheck,
    sendChat,
    getDepartments,
    getDepartment,
    sendDepartmentChat,
    sendDepartmentTrainerChat,
    API_URL,
} from '../backend';

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
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: async () => {
                    throw new Error('not json');
                },
                text: async () => 'server error',
            });

            await expect(sendChat('fail')).rejects.toThrow('Chat failed');
        });
    });

    describe('department APIs', () => {
        it('getDepartments() fetches all departments', async () => {
            const payload = [{
                id: 'hr',
                name: 'Human Resources',
                description: 'desc',
                info: 'info',
                persona_system_prompt: 'persona',
                trainer_persona_prompt: 'trainer persona',
            }];
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => payload,
            });

            const result = await getDepartments();

            expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/api/v1/departments/`, { cache: 'no-store' });
            expect(result).toEqual(payload);
        });

        it('getDepartment() fetches one department', async () => {
            const payload = {
                id: 'it',
                name: 'IT Support',
                description: 'desc',
                info: 'info',
                persona_system_prompt: 'persona',
                trainer_persona_prompt: 'trainer persona',
            };
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => payload,
            });

            const result = await getDepartment('it');

            expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/api/v1/departments/it`, { cache: 'no-store' });
            expect(result).toEqual(payload);
        });

        it('sendDepartmentChat() posts to the department chat endpoint', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ answer: 'A' }),
            });

            await sendDepartmentChat('sales', 'How do I prospect?', ['q1']);

            expect(global.fetch).toHaveBeenCalledWith(
                `${API_URL}/api/v1/departments/sales/chat`,
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: 'How do I prospect?', history: ['q1'] }),
                })
            );
        });

        it('sendDepartmentTrainerChat() posts to the department trainer endpoint', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ answer: 'B' }),
            });

            await sendDepartmentTrainerChat('marketing', 'How do I run a campaign?', ['q2']);

            expect(global.fetch).toHaveBeenCalledWith(
                `${API_URL}/api/v1/departments/marketing/trainer`,
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: 'How do I run a campaign?', history: ['q2'] }),
                })
            );
        });
    });
});
