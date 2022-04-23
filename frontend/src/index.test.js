const test = require('tape')

test('Test equal', t => {
    t.equal('index', 'index')
    t.end()
})

test('Test ok', t => {
    t.ok(1 > 0)
    t.end()
})

test('Test true', t => {
    t.true(true)
    t.end()
})

test('Test false', t => {
    t.false(false)
    t.end()
})