CREATE TABLE answer (
	answer_id text primary key on conflict replace,
	assignment_id text,
	task_id text,
	answer_type text,
	free_text text,
	selection_id text,
	other_selection_text text,
	uploaded_file_key text,
	uploaded_file_size integer
);
CREATE TABLE assignment (
	assignment_id text primary key on conflict replace,
	worker_id text not null,
	hit_id text not null,
	assignment_status text,
	auto_approval_time text,
	accept_time text,
	submit_time text,
	approval_time text,
	rejection_time text,
	requester_feedback text
);
CREATE TABLE bonus (
	bonus_id integer primary key,
	assignment_id text,
	worker_id text,
	amount real,
	currency text,
	payment_time text,
	reason text
);
CREATE TABLE hit (
	hit_id text primary key,
	hit_type_id text,
	question_xml text,
	creation_time text,
	hit_status text,
	expiration_time text,
	max_assignments integer,
	requester_annotation text,
	hit_review_status text,
	num_pending integer,
	num_available integer,
	num_completed integer,
	approximate_expiration_time text
);
CREATE TABLE hit_type (
	hit_type_id text primary key,
	title text,
	description text,
	keywords text,
	reward_amount real,
	reward_currency text,
	assignment_duration integer,
	auto_approval_delay integer
);
CREATE TABLE hit_type_qualification_requirement (
	hit_type_qualification_requirement_id integer primary key,
	hit_type_id text,
	qualification_type_id text,
	comparator text,
	integer_value integer,
	locale_value text,
	required_to_preview integer
);
CREATE TABLE notification_hit_type (
        hit_type_id text primary key,
        registered_time text not null,
        last_received_time text,
        is_connected integer
);
CREATE TABLE notification_status (
        url text not null,
        test_received_time text
);
CREATE TABLE qualification_type (
	qualification_type_id text primary key,
	creation_time text,
	name text,
	description text,
	keywords text,
	is_active integer,
	retry_delay integer,
	test_xml text,
	test_duration integer,
	answer_key_xml text,
	auto_granted integer,
	auto_granted_value integer,
	is_requestable integer
);
CREATE TABLE sent_mail (
	sent_mail_id integer primary key,
	worker_id text,
	assignment_id text,
	send_time datetime,
	subject text,
	message_text text
);
