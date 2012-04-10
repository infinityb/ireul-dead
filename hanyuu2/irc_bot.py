from flyrc import client, handler

cli = client.SimpleClient('NotHanyuu', 'nothanyuu', '/a/radio bot',
                          '10.0.12.6', 6697, ssl=True, timeout=None)

cli.add_handler(handler.AutoJoin('#everfree'))
cli.add_handler(handler.BasicChannelCommand(prefix='!'))
cli.add_handler(handler.QuitWhenAsked())

