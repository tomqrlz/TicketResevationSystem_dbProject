create function countReservation(Id int) returns int
begin
	declare val int;
	select count(reservationId) into val from `reservation` where `match` IN select matchId from `matchSchedule` where matchweekNo = Id;
	return val;
end;
