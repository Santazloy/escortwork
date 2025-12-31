-- Схема базы данных для учета балансов в Telegram группах
-- Создайте эти таблицы в Supabase SQL Editor

-- Таблица для хранения текущих балансов групп
CREATE TABLE IF NOT EXISTS group_balances (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL UNIQUE,
    group_name VARCHAR(255),
    current_balance DECIMAL(15, 2) DEFAULT 0.00,
    language VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица для истории всех транзакций
CREATE TABLE IF NOT EXISTS balance_transactions (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    user_id BIGINT,
    username VARCHAR(255),
    amount DECIMAL(15, 2) NOT NULL,
    previous_balance DECIMAL(15, 2) NOT NULL,
    new_balance DECIMAL(15, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- 'add' or 'subtract'
    message_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (group_id) REFERENCES group_balances(group_id) ON DELETE CASCADE
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_balance_transactions_group_id ON balance_transactions(group_id);
CREATE INDEX IF NOT EXISTS idx_balance_transactions_created_at ON balance_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_group_balances_group_id ON group_balances(group_id);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_group_balances_updated_at
    BEFORE UPDATE ON group_balances
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Инициализация балансов для трёх групп
-- ВАЖНО: Замените ID на реальные ID ваших Telegram групп
-- Получить ID группы можно добавив бота @userinfobot в группу
--
-- Группы по умолчанию:
--   GROUP_RU_ID:         -1002774266933  (Русская группа Shanghai)
--   GROUP_ZH_ID:         -1002468561827  (Китайская группа Shanghai)
--   GROUP_ZH_BEIJING_ID: -1003698590476  (Китайская группа Beijing)
INSERT INTO group_balances (group_id, group_name, current_balance, language)
VALUES
    (-1002774266933, 'Русская группа (Shanghai)', 0.00, 'ru'),
    (-1002468561827, '上海中文群组', 0.00, 'zh'),
    (-1003698590476, '北京中文群组', 0.00, 'zh')
ON CONFLICT (group_id) DO NOTHING;

-- Комментарии к таблицам
COMMENT ON TABLE group_balances IS 'Текущие балансы групп Telegram';
COMMENT ON TABLE balance_transactions IS 'История всех транзакций балансов';
COMMENT ON COLUMN group_balances.language IS 'Язык сообщений: ru (русский) или zh (китайский)';
COMMENT ON COLUMN balance_transactions.transaction_type IS 'Тип транзакции: add (пополнение) или subtract (списание)';