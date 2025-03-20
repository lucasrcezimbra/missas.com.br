const wppconnect = require('@wppconnect-team/wppconnect');

async function main() {
	const client = await wppconnect.create({ headless: false, whatsappVersion: '2.3000.1019760984-alpha' });
	const chats = await client.listChats();
	const unarchivedChats = chats.filter((c) => !c.archive && !c.contact.isMe);

	for (const chat of unarchivedChats) {
	    const messages = await client.getMessages(chat.id);
	    const formattedMessages = [];

	    messages.forEach((message) => {
		const { timestamp, from, body, sender } = message;
		if (!body) return;

		const date = new Date(timestamp * 1000);
		const timeString = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
		const dateString = date.toLocaleDateString('pt-BR');
		const contactNumber = sender ? sender.formattedName : from.replace('@c.us', '');
		const formattedMessage = `[${timeString}, ${dateString}] ${contactNumber}:\n${body}`;
		formattedMessages.push(formattedMessage);
	    });

	    if (formattedMessages.length === 0) continue;

	    const chatStr = formattedMessages.join('\n');
	    const phone = chat.id.user;
	    console.log(`poetry run python contrib/import.py '+${phone}' '${chatStr}'`);
	}
}

main();
