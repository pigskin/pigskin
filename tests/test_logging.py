from ..pigskin import pigskin

gp = pigskin(debug=True)


def test_passing(capsys):
    assert gp.debug == True

def test_debugging_off(capsys):
    gp.debug = False
    gp.log('The sound of silence.')

    captured = capsys.readouterr()
    assert captured.out == ''

def test_normal(capsys):
    gp.debug = True
    gp.log('I like tacos'.encode('ascii'))

    captured = capsys.readouterr()
    assert captured.out == '[pigskin]: I like tacos\n'

def test_ascii(capsys):
    gp.debug = True
    gp.log('I like tacos'.encode('ascii'))

    captured = capsys.readouterr()
    assert captured.out == '[pigskin]: I like tacos\n'

def test_unicode(capsys):
    gp.debug = True
    gp.log(u'I like tacos')

    captured = capsys.readouterr()
    assert captured.out == '[pigskin]: I like tacos\n'

def test_BOM(capsys):
    gp.debug = True
    gp.log(b'\xef\xbb\xbfBOM.')

    captured = capsys.readouterr()
    assert captured.out == '[pigskin]: BOM.\n'
