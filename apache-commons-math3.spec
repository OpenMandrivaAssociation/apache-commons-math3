Name:		apache-commons-math3
Version:	3.6.1
Release:	1
Summary:	Mathematics and statistics library
Group:		Development/Java
License:	ASL 2.0
URL:		https://commons.apache.org/proper/commons-math/
Source0:	https://archive.apache.org/dist/commons/math/source/commons-math3-%{version}-src.tar.gz

BuildArch:	noarch
BuildRequires:	python
BuildRequires:	mvn(org.apache.commons:commons-parent:pom::)
BuildRequires:	mvn(org.apache:apache:pom::)
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name commons-math3 --link %{name} --alias org.apache.commons:commons-math3

%description
Apache Commons Math 3 is a library of mathematics and statistics
components. 3.6.1 fixes ODE integrators when several events fire
together. This is the org.apache.commons:commons-math3 artifact, a
different API from Commons Math 2. The build targets Java 8 and skips
tests. The tools classifier jar is not shipped. The automatic module
name is org.apache.commons.math3.

%prep
%autosetup -n commons-math3-%{version}-src
# The package-phase antrun builds a tools classifier from test classes.
# The site-checkout profile is active when site-content is absent, and
# antrun is on the sysjar keep list, so both plugin blocks are removed.
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def local(tag):
    return tag.rsplit("}", 1)[-1]

path = Path("pom.xml")
tree = ET.parse(path)
root = tree.getroot()
bumped = 0
for node in root.iter():
    name = local(node.tag)
    if name in ("maven.compiler.source", "maven.compiler.target"):
        if (node.text or "").strip() != "1.5":
            raise SystemExit("unexpected compiler level " + (node.text or ""))
        node.text = "1.8"
        bumped += 1
if bumped != 2:
    raise SystemExit("compiler properties not found")
removed_deps = []
for parent in list(root.iter()):
    if local(parent.tag) != "dependencies":
        continue
    for child in list(parent):
        if local(child.tag) != "dependency":
            continue
        scope = artifact = ""
        for item in child:
            item_name = local(item.tag)
            if item_name == "scope":
                scope = (item.text or "").strip()
            elif item_name == "artifactId":
                artifact = (item.text or "").strip()
        if scope == "test":
            parent.remove(child)
            removed_deps.append(artifact)
if removed_deps != ["junit"]:
    raise SystemExit("unexpected dependency edit: " + " ".join(removed_deps))
removed_plugins = []
for parent in list(root.iter()):
    for child in list(parent):
        if local(child.tag) != "plugin":
            continue
        artifact = ""
        for item in child:
            if local(item.tag) == "artifactId":
                artifact = (item.text or "").strip()
        if artifact in ("maven-antrun-plugin", "build-helper-maven-plugin"):
            parent.remove(child)
            removed_plugins.append(artifact)
if sorted(removed_plugins) != ["build-helper-maven-plugin", "maven-antrun-plugin", "maven-antrun-plugin"]:
    raise SystemExit("unexpected plugin edit: " + " ".join(sorted(removed_plugins)))
removed_reporting = 0
for child in list(root):
    if local(child.tag) == "reporting":
        root.remove(child)
        removed_reporting += 1
if removed_reporting != 1:
    raise SystemExit("reporting edit failed")
tree.write(path, encoding="UTF-8", xml_declaration=True)
text = path.read_text(encoding="utf-8")
for needle in ("maven-antrun-plugin", "build-helper-maven-plugin", "<scope>test</scope>", "<reporting>", "<artifactId>junit</artifactId>"):
    if needle in text:
        raise SystemExit("pom still contains " + needle)
if "<maven.compiler.source>1.8</maven.compiler.source>" not in text:
    raise SystemExit("compiler source missing")
if "<maven.compiler.target>1.8</maven.compiler.target>" not in text:
    raise SystemExit("compiler target missing")
PY

%build -a
cat > manifest-addition <<'EOF'
Automatic-Module-Name: org.apache.commons.math3
EOF
jar ufm target/commons-math3-%{version}.jar manifest-addition
java --module-path target/commons-math3-%{version}.jar --describe-module org.apache.commons.math3 | grep -q '^org.apache.commons.math3'

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt RELEASE-NOTES.txt
