from django.db import migrations


def seed_data(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    Tag = apps.get_model('catalog', 'Tag')
    Product = apps.get_model('catalog', 'Product')

    # ── Categories ──────────────────────────────────────────
    electrical_wiring   = Category.objects.create(name='Electrical Wiring')
    conduit_fittings    = Category.objects.create(name='Conduit & Fittings')
    circuit_protection  = Category.objects.create(name='Circuit Protection')
    lighting_controls   = Category.objects.create(name='Lighting & Controls')
    tools_equipment     = Category.objects.create(name='Tools & Equipment')

    # ── Tags ────────────────────────────────────────────────
    tags = {}
    for tag_name in [
        'in-stock', 'prefab-ready', 'UL-listed', 'bulk-discount',
        'outdoor-rated', 'high-voltage', 'low-voltage',
        'hazardous-location', 'new-arrival', 'discontinued',
    ]:
        tags[tag_name] = Tag.objects.create(name=tag_name)

    # ── Products ─────────────────────────────────────────────
    products = [
        {
            'name': '12 AWG THHN Copper Wire',
            'sku': 'WR-001',
            'description': '12 AWG THHN/THWN copper wire for general wiring in conduit, rated 90°C dry/75°C wet.',
            'unit_of_measure': 'spool',
            'category': electrical_wiring,
            'tags': ['in-stock', 'UL-listed', 'bulk-discount'],
        },
        {
            'name': '14 AWG THHN Copper Wire',
            'sku': 'WR-002',
            'description': '14 AWG THHN copper wire, 500ft spool, suitable for branch circuits.',
            'unit_of_measure': 'spool',
            'category': electrical_wiring,
            'tags': ['in-stock', 'UL-listed'],
        },
        {
            'name': '10 AWG THHN Copper Wire',
            'sku': 'WR-003',
            'description': '10 AWG THHN copper wire for higher ampacity branch circuits.',
            'unit_of_measure': 'spool',
            'category': electrical_wiring,
            'tags': ['in-stock', 'UL-listed', 'bulk-discount'],
        },
        {
            'name': '3-Conductor 12 AWG NM-B Cable',
            'sku': 'WR-004',
            'description': 'Romex-style NM-B cable for residential wiring, 250ft roll.',
            'unit_of_measure': 'roll',
            'category': electrical_wiring,
            'tags': ['in-stock', 'UL-listed'],
        },
        {
            'name': '1" EMT Conduit',
            'sku': 'CF-001',
            'description': '1 inch EMT steel conduit, 10ft length for indoor/outdoor wiring protection.',
            'unit_of_measure': 'each',
            'category': conduit_fittings,
            'tags': ['in-stock', 'outdoor-rated'],
        },
        {
            'name': '3/4" EMT Conduit',
            'sku': 'CF-002',
            'description': '3/4 inch EMT steel conduit, 10ft length.',
            'unit_of_measure': 'each',
            'category': conduit_fittings,
            'tags': ['in-stock', 'outdoor-rated'],
        },
        {
            'name': '1" EMT Compression Coupling',
            'sku': 'CF-003',
            'description': 'Steel compression coupling for joining 1 inch EMT conduit sections.',
            'unit_of_measure': 'each',
            'category': conduit_fittings,
            'tags': ['in-stock', 'UL-listed'],
        },
        {
            'name': '1" PVC Conduit 90° Elbow',
            'sku': 'CF-004',
            'description': 'Schedule 40 PVC elbow for underground or exposed PVC conduit runs.',
            'unit_of_measure': 'each',
            'category': conduit_fittings,
            'tags': ['in-stock', 'outdoor-rated'],
        },
        {
            'name': '20A Single-Pole Circuit Breaker',
            'sku': 'CP-001',
            'description': '20A 120V single-pole thermal magnetic circuit breaker, plug-on neutral compatible.',
            'unit_of_measure': 'each',
            'category': circuit_protection,
            'tags': ['in-stock', 'UL-listed', 'prefab-ready'],
        },
        {
            'name': '20A Dual-Pole Circuit Breaker',
            'sku': 'CP-002',
            'description': '20A 240V dual-pole circuit breaker for HVAC and appliance circuits.',
            'unit_of_measure': 'each',
            'category': circuit_protection,
            'tags': ['in-stock', 'UL-listed'],
        },
        {
            'name': '20A GFCI Outlet Breaker',
            'sku': 'CP-003',
            'description': '20A GFCI circuit breaker for bathroom, kitchen, and outdoor circuit protection.',
            'unit_of_measure': 'each',
            'category': circuit_protection,
            'tags': ['in-stock', 'UL-listed', 'outdoor-rated'],
        },
        {
            'name': '100A Main Breaker Panel',
            'sku': 'CP-004',
            'description': '100A 120/240V main breaker load center, 20-space 40-circuit indoor panel.',
            'unit_of_measure': 'each',
            'category': circuit_protection,
            'tags': ['in-stock', 'UL-listed', 'high-voltage'],
        },
        {
            'name': '200A Main Breaker Panel',
            'sku': 'CP-005',
            'description': '200A 120/240V main breaker load center, 40-space 80-circuit indoor panel.',
            'unit_of_measure': 'each',
            'category': circuit_protection,
            'tags': ['UL-listed', 'high-voltage', 'new-arrival'],
        },
        {
            'name': 'LED High Bay Light 150W',
            'sku': 'LC-001',
            'description': '150W LED high bay light fixture for warehouse and industrial applications, 5000K.',
            'unit_of_measure': 'each',
            'category': lighting_controls,
            'tags': ['in-stock', 'UL-listed', 'prefab-ready'],
        },
        {
            'name': 'LED Strip Light 12V',
            'sku': 'LC-002',
            'description': '12V DC LED strip light, 16ft roll, 3000K warm white, low voltage rated.',
            'unit_of_measure': 'roll',
            'category': lighting_controls,
            'tags': ['in-stock', 'low-voltage'],
        },
        {
            'name': 'Occupancy Sensor Switch',
            'sku': 'LC-003',
            'description': 'Single-pole passive infrared occupancy sensor wall switch, 120V 15A.',
            'unit_of_measure': 'each',
            'category': lighting_controls,
            'tags': ['in-stock', 'UL-listed', 'new-arrival'],
        },
        {
            'name': 'Dimmer Switch 600W',
            'sku': 'LC-004',
            'description': 'Single-pole 600W incandescent and LED compatible dimmer switch, ivory.',
            'unit_of_measure': 'each',
            'category': lighting_controls,
            'tags': ['in-stock', 'UL-listed'],
        },
        {
            'name': 'Klein Tools Electrician Pliers',
            'sku': 'TE-001',
            'description': '9 inch high-leverage side-cutting pliers, chrome vanadium steel, for electrical work.',
            'unit_of_measure': 'each',
            'category': tools_equipment,
            'tags': ['in-stock', 'prefab-ready'],
        },
        {
            'name': 'Fish Tape 50ft Steel',
            'sku': 'TE-002',
            'description': '50ft steel fish tape with ergonomic reel case for pulling wire through conduit.',
            'unit_of_measure': 'each',
            'category': tools_equipment,
            'tags': ['in-stock'],
        },
        {
            'name': 'Voltage Tester Non-Contact',
            'sku': 'TE-003',
            'description': 'Non-contact AC voltage tester, detects 12-1000V AC, with LED and audible alert.',
            'unit_of_measure': 'each',
            'category': tools_equipment,
            'tags': ['in-stock', 'UL-listed', 'new-arrival'],
        },
    ]

    for product_data in products:
        tag_names = product_data.pop('tags')
        product = Product.objects.create(**product_data)
        product.tags.set([tags[t] for t in tag_names])


def unseed_data(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    Tag = apps.get_model('catalog', 'Tag')
    Product = apps.get_model('catalog', 'Product')
    Product.objects.all().delete()
    Tag.objects.all().delete()
    Category.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]