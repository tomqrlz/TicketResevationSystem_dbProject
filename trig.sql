DELIMITER //
Create Trigger upd_login
BEFORE UPDATE ON users FOR EACH ROW
BEGIN
IF NEW.userLogin = OLD.userLogin THEN
SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'same name';
ELSEIF NEW.userLogin in (select userLogin from users) THEN
SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'same name in database';
END IF;
END //